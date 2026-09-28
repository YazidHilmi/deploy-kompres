"""Alur utama untuk membuat prediksi produksi."""

from __future__ import annotations

import time

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app_services import get_engine, get_tabpfn_model, load_index_history
from src.database import get_prediction, save_prediction
from src.features import build_feature_row, get_available_target_periods
from src.model import predict_production
from src.reports import build_prediction_pdf
from src.schemas import SUPPORTED_REGIONS
from src.ui import apply_theme, format_number, format_period, format_ton, page_header


apply_theme()
page_header(
    "Prediksi produksi padi",
    "Pilih wilayah dan periode untuk memperoleh prediksi produksi berdasarkan data vegetasi Sentinel-2 dan model AI.",
    "Analisis Baru",
)

try:
    engine = get_engine()
    history = load_index_history()
except Exception as error:
    st.error(f"Data belum dapat dimuat: {error}")
    st.stop()

selector_col, context_col = st.columns([1, 1.35], gap="large")
with selector_col:
    st.subheader("Tentukan analisis")
    kabupaten = st.selectbox("Kabupaten", SUPPORTED_REGIONS)
    available_periods = get_available_target_periods(history, kabupaten)
    if not available_periods:
        st.warning("Belum ada periode yang siap diproses untuk wilayah ini.")
        st.stop()
    target_period = st.selectbox(
        "Periode prediksi", list(reversed(available_periods)), format_func=format_period,
    )
    run_prediction = st.button("Jalankan prediksi", type="primary", width="stretch")

with context_col:
    st.subheader("Data yang digunakan")
    target_months = [target_period - 2, target_period - 1, target_period]
    chart_data = history[
        (history["Kabupaten"] == kabupaten) & history["Period"].isin(target_months)
    ].copy()
    chart_data["Periode"] = chart_data["Period"].map(format_period)
    chart_long = chart_data.melt(
        id_vars=["Periode"], value_vars=["NDVI_mean", "EVI_mean", "SAVI_mean"],
        var_name="Indeks", value_name="Nilai",
    )
    chart_long["Indeks"] = chart_long["Indeks"].str.replace("_mean", "", regex=False)
    figure = px.line(
        chart_long, x="Periode", y="Nilai", color="Indeks", markers=True,
        color_discrete_map={"NDVI": "#1f6b45", "EVI": "#d79a35", "SAVI": "#5a7894"},
    )
    figure.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend_title_text="Indeks")
    st.plotly_chart(figure, width="stretch")
    st.caption("Observasi vegetasi tiga bulan yang menjadi data pendukung prediksi.")

if run_prediction:
    started_at = time.perf_counter()
    try:
        with st.status("Menyiapkan dan menjalankan model...", expanded=True) as status:
            st.write("Memeriksa kelengkapan data wilayah dan periode.")
            features = build_feature_row(history, kabupaten, target_period)
            st.write("Menjalankan model prediksi produksi.")
            model, _ = get_tabpfn_model()
            prediction = float(predict_production(model, features)[0])
            processing_seconds = time.perf_counter() - started_at
            prediction_id = save_prediction(
                engine, kabupaten=kabupaten, target_period=target_period,
                estimated_production_ton=prediction, model_version="TabPFN Client 3.5",
                index_source="Sentinel-2 / Google Earth Engine",
                input_features=features.iloc[0].to_dict(), processing_seconds=processing_seconds,
            )
            status.update(label="Prediksi berhasil dibuat", state="complete", expanded=False)
        st.session_state["latest_prediction_id"] = prediction_id
    except Exception as error:
        st.error(f"Prediksi belum berhasil diproses: {error}")

prediction_id = st.session_state.get("latest_prediction_id")
record = get_prediction(engine, prediction_id) if prediction_id else None

if record:
    st.divider()
    st.subheader("Hasil prediksi")
    st.markdown(
        f"""
        <section class="padi-result">
          <div class="padi-muted">{record['kabupaten']} · {format_period(record['target_period'])}</div>
          <div class="value">{format_ton(record['estimated_production_ton'], 2)}</div>
          <div class="padi-muted">Prediksi produksi padi pada periode terpilih</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    current_period = pd.Period(record["target_period"], freq="M")
    support = history[
        (history["Kabupaten"] == record["kabupaten"])
        & history["Period"].isin([current_period - 2, current_period - 1, current_period])
    ].copy()
    with st.expander("Lihat data pendukung prediksi"):
        st.caption("Nilai berikut merupakan observasi Sentinel-2, bukan keluaran prediksi model.")
        support["Periode"] = support["Period"].map(format_period)
        display_support = support[["Periode", "NDVI_mean", "EVI_mean", "SAVI_mean"]].rename(columns={
            "NDVI_mean": "NDVI", "EVI_mean": "EVI", "SAVI_mean": "SAVI",
        })
        st.dataframe(display_support, hide_index=True, width="stretch")

    report_record = dict(record)
    report_record["index_history"] = support
    csv_row = pd.DataFrame([{
        "Kabupaten": record["kabupaten"], "Periode": str(record["target_period"])[:7],
        "Prediksi Produksi (ton)": round(record["estimated_production_ton"], 2),
        "Status Data": "Lengkap",
    }])
    download_col1, download_col2 = st.columns(2)
    download_col1.download_button(
        "Unduh hasil CSV", csv_row.to_csv(index=False).encode("utf-8"),
        file_name=f"prediksi_{record['kabupaten'].lower()}_{current_period}.csv",
        mime="text/csv", width="stretch",
    )
    download_col2.download_button(
        "Unduh laporan PDF", build_prediction_pdf(report_record),
        file_name=f"laporan_{record['kabupaten'].lower()}_{current_period}.pdf",
        mime="application/pdf", width="stretch",
    )

    st.success("Hasil telah disimpan dan tersedia pada halaman Riwayat & Laporan.")
