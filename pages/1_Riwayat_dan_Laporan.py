"""Halaman riwayat hasil permanen dan laporan PDF."""

import os

import pandas as pd
import streamlit as st

from src.database import create_database_engine, get_prediction, initialize_database, list_predictions
from src.reports import build_prediction_pdf
from src.schemas import SUPPORTED_REGIONS


def get_database_url():
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    try:
        return st.secrets["DATABASE_URL"] or None
    except (KeyError, FileNotFoundError):
        return None


@st.cache_resource
def get_engine(database_url):
    engine = create_database_engine(database_url)
    initialize_database(engine)
    return engine


st.title("Riwayat dan Laporan")
st.caption("Hasil prediksi tersimpan permanen dan dapat diunduh kembali sebagai CSV atau PDF.")

engine = get_engine(get_database_url())
region_filter = st.selectbox("Filter kabupaten", ["Semua", *SUPPORTED_REGIONS])
history = list_predictions(engine, None if region_filter == "Semua" else region_filter)

if history.empty:
    st.info("Belum ada hasil tersimpan. Jalankan prediksi dari halaman utama terlebih dahulu.")
    st.stop()

display = history.drop(columns=["input_features"]).rename(columns={
    "id": "ID", "kabupaten": "Kabupaten", "target_period": "Bulan Target",
    "estimated_production_ton": "Estimasi Produksi (ton)", "model_version": "Model",
    "index_source": "Sumber Indeks", "quality_status": "Status",
    "processing_seconds": "Waktu (detik)", "created_at": "Dibuat",
})
st.dataframe(display, width="stretch", hide_index=True)

labels = {
    row["id"]: f'{row["kabupaten"]} · {str(row["target_period"])[:7]} · {row["estimated_production_ton"]:,.2f} ton · {row["id"][:8]}'
    for _, row in history.iterrows()
}
selected_id = st.selectbox("Pilih hasil untuk laporan", history["id"].tolist(), format_func=labels.get)
record = get_prediction(engine, selected_id)

col1, col2, col3 = st.columns(3)
col1.metric("Estimasi Produksi", f'{record["estimated_production_ton"]:,.2f} ton')
col2.metric("Kabupaten", record["kabupaten"])
col3.metric("Bulan Target", str(record["target_period"])[:7])

download_row = pd.DataFrame([{
    "ID_Hasil": record["id"], "Kabupaten": record["kabupaten"],
    "Bulan_Target": record["target_period"],
    "Estimasi_Produksi_Ton": record["estimated_production_ton"],
    "Model": record["model_version"], "Sumber_Indeks": record["index_source"],
    "Status": record["quality_status"], "Dibuat": record["created_at"],
}])
download_col1, download_col2 = st.columns(2)
download_col1.download_button(
    "Unduh Hasil CSV", download_row.to_csv(index=False).encode("utf-8"),
    file_name=f"hasil_{record['id'][:8]}.csv", mime="text/csv", width="stretch",
)
download_col2.download_button(
    "Unduh Laporan PDF", build_prediction_pdf(record),
    file_name=f"laporan_{record['id'][:8]}.pdf", mime="application/pdf", width="stretch",
)

with st.expander("Lihat fitur model"):
    st.dataframe(pd.DataFrame([record["input_features"]]), width="stretch", hide_index=True)
