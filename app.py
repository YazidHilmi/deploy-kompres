import os
import time

import pandas as pd
import plotly.express as px
import streamlit as st

from src.artifacts import load_training_artifacts
from src.config import HISTORICAL_INDEX_PATH
from src.database import (
    create_database_engine, initialize_database, load_monthly_indices, save_prediction, seed_monthly_indices,
)
from src.features import (
    build_feature_row,
    get_available_target_periods,
    prepare_index_history,
)
from src.model import fit_model, predict_production
from src.reports import build_prediction_pdf
from src.schemas import SUPPORTED_REGIONS


st.set_page_config(
    page_title="Prediksi Produksi Padi",
    page_icon="🌾",
    layout="wide",
)


def get_secret(name):
    value = os.getenv(name)

    if value:
        return value

    try:
        return st.secrets[name]
    except (KeyError, FileNotFoundError):
        return None


@st.cache_data
def load_historical_indices():
    frame = pd.read_csv(HISTORICAL_INDEX_PATH)
    return prepare_index_history(frame)


@st.cache_resource
def load_tabpfn_model():
    artifacts = load_training_artifacts()
    token = get_secret("TABPFN_TOKEN")

    model = fit_model(
        X_train=artifacts["X_train"],
        y_train=artifacts["y_train"],
        best_params=artifacts["best_params"],
        access_token=token,
    )

    return model, artifacts


@st.cache_resource
def initialize_data_store(database_url):
    engine = create_database_engine(database_url)
    initialize_database(engine)
    seed_monthly_indices(engine, load_historical_indices())
    return engine


st.title("🌾 Prediksi Produksi Padi")
st.caption(
    "Estimasi produksi bulanan berbasis NDVI, EVI, SAVI, "
    "dan TabPFN."
)

try:
    reference_history = load_historical_indices()
    database_engine = initialize_data_store(get_secret("DATABASE_URL"))
    history = prepare_index_history(load_monthly_indices(database_engine))
except Exception as error:
    st.error(f"Gagal memuat data indeks: {error}")
    st.stop()


kabupaten = st.selectbox(
    "Kabupaten",
    options=SUPPORTED_REGIONS,
)

available_periods = get_available_target_periods(
    history=history,
    kabupaten=kabupaten,
)

if not available_periods:
    st.warning(
        "Belum ada periode dengan data tiga bulan lengkap."
    )
    st.stop()

target_period = st.selectbox(
    "Bulan target",
    options=list(reversed(available_periods)),
    format_func=lambda period: period.strftime("%B %Y"),
)

target_months = [
    target_period - 2,
    target_period - 1,
    target_period,
]

chart_data = history[
    (history["Kabupaten"] == kabupaten)
    & (history["Period"].isin(target_months))
].copy()

chart_data["Periode"] = chart_data["Period"].astype(str)

st.subheader("Kondisi vegetasi yang digunakan")

chart_long = chart_data.melt(
    id_vars=["Periode"],
    value_vars=["NDVI_mean", "EVI_mean", "SAVI_mean"],
    var_name="Indeks",
    value_name="Nilai",
)

chart = px.line(
    chart_long,
    x="Periode",
    y="Nilai",
    color="Indeks",
    markers=True,
)

st.plotly_chart(chart, width="stretch")

if st.button(
    "Buat Prediksi",
    type="primary",
    width="stretch",
):
    started_at = time.perf_counter()

    try:
        with st.status(
            "Menjalankan prediksi...",
            expanded=True,
        ) as status:
            st.write("Membentuk 18 fitur model...")

            features = build_feature_row(
                history=history,
                kabupaten=kabupaten,
                target_period=target_period,
            )

            st.write("Memuat TabPFN...")
            model, artifacts = load_tabpfn_model()

            st.write("Mengestimasi produksi...")
            prediction = predict_production(
                model=model,
                features=features,
            )[0]

            status.update(
                label="Prediksi selesai.",
                state="complete",
                expanded=False,
            )

        processing_seconds = time.perf_counter() - started_at

        prediction_id = save_prediction(
            database_engine,
            kabupaten=kabupaten,
            target_period=target_period,
            estimated_production_ton=prediction,
            model_version="TabPFN Client 3.5",
            index_source="historis_index.csv",
            input_features=features.iloc[0].to_dict(),
            processing_seconds=processing_seconds,
        )

        st.success("Prediksi berhasil dibuat.")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Estimasi Produksi",
            f"{prediction:,.2f} ton",
        )

        col2.metric(
            "Kabupaten",
            kabupaten,
        )

        col3.metric(
            "Periode",
            str(target_period),
        )

        st.caption(
            f"Waktu pemrosesan: {processing_seconds:.2f} detik · ID hasil: {prediction_id}"
        )

        current_index = chart_data[
            chart_data["Period"] == target_period
        ].iloc[0]

        index_col1, index_col2, index_col3 = st.columns(3)

        index_col1.metric(
            "NDVI",
            f"{current_index['NDVI_mean']:.4f}",
        )

        index_col2.metric(
            "EVI",
            f"{current_index['EVI_mean']:.4f}",
        )

        index_col3.metric(
            "SAVI",
            f"{current_index['SAVI_mean']:.4f}",
        )

        result = pd.DataFrame([{
            "ID_Hasil": prediction_id,
            "Kabupaten": kabupaten,
            "Tahun": target_period.year,
            "Bulan": target_period.month,
            "Estimasi_Produksi_Ton": prediction,
            "NDVI_mean": current_index["NDVI_mean"],
            "EVI_mean": current_index["EVI_mean"],
            "SAVI_mean": current_index["SAVI_mean"],
            "Sumber_Data": "historis_index.csv",
            "Waktu_Pemrosesan_Detik": processing_seconds,
        }])

        st.download_button(
            "Unduh Hasil CSV",
            data=result.to_csv(index=False).encode("utf-8"),
            file_name=(
                f"prediksi_{kabupaten.lower()}_"
                f"{target_period}.csv"
            ),
            mime="text/csv",
            width="stretch",
        )

        report_record = {
            "id": prediction_id, "kabupaten": kabupaten,
            "target_period": target_period.to_timestamp().date(),
            "estimated_production_ton": prediction, "model_version": "TabPFN Client 3.5",
            "index_source": "historis_index.csv", "input_features": features.iloc[0].to_dict(),
            "quality_status": "valid", "processing_seconds": processing_seconds,
            "created_at": pd.Timestamp.now(),
        }
        st.download_button(
            "Unduh Laporan PDF", data=build_prediction_pdf(report_record),
            file_name=f"laporan_{prediction_id[:8]}.pdf", mime="application/pdf",
            width="stretch",
        )

        with st.expander("Lihat 18 fitur model"):
            st.dataframe(
                features,
                width="stretch",
            )

    except Exception as error:
        st.error(f"Prediksi gagal: {error}")
