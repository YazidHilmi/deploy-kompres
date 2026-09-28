"""Riwayat prediksi permanen dan pusat unduhan laporan."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app_services import get_engine, load_index_history
from src.database import get_prediction, list_predictions
from src.reports import build_prediction_pdf
from src.schemas import SUPPORTED_REGIONS
from src.ui import apply_theme, format_period, format_ton, page_header


apply_theme()
page_header(
    "Riwayat dan laporan",
    "Telusuri hasil prediksi yang pernah dibuat, lihat perkembangannya, dan unduh kembali laporan.",
    "Arsip Prediksi",
)

engine, index_history = get_engine(), load_index_history()
history = list_predictions(engine)
if history.empty:
    st.info("Belum ada prediksi tersimpan. Buat prediksi pertama dari halaman Prediksi Produksi.")
    if st.button("Buka Prediksi Produksi", type="primary"):
        st.switch_page("pages/1_Prediksi_Produksi.py")
    st.stop()

history["target_period"] = pd.to_datetime(history["target_period"])
history["created_at"] = pd.to_datetime(history["created_at"])
filter_col1, filter_col2 = st.columns([1, 2])
region_filter = filter_col1.selectbox("Kabupaten", ["Semua", *SUPPORTED_REGIONS])
period_bounds = filter_col2.date_input(
    "Rentang periode", value=(history["target_period"].min().date(), history["target_period"].max().date()),
)

filtered = history.copy()
if region_filter != "Semua":
    filtered = filtered[filtered["kabupaten"] == region_filter]
if isinstance(period_bounds, (tuple, list)) and len(period_bounds) == 2:
    start, end = pd.Timestamp(period_bounds[0]), pd.Timestamp(period_bounds[1])
    filtered = filtered[filtered["target_period"].between(start, end)]

st.caption(f"Menampilkan {len(filtered)} hasil prediksi.")
if filtered.empty:
    st.warning("Tidak ada hasil pada filter yang dipilih.")
    st.stop()

chart_data = filtered.sort_values("target_period").copy()
chart_data["Periode"] = chart_data["target_period"].dt.strftime("%Y-%m")
figure = px.line(
    chart_data, x="Periode", y="estimated_production_ton", color="kabupaten", markers=True,
    labels={"estimated_production_ton": "Prediksi produksi (ton)", "kabupaten": "Kabupaten"},
    color_discrete_sequence=["#1f6b45", "#4f8f65", "#d79a35", "#5a7894", "#856b8f"],
)
figure.update_layout(margin=dict(l=10, r=10, t=20, b=10), legend_title_text="Kabupaten")
st.plotly_chart(figure, width="stretch")

display = filtered[["kabupaten", "target_period", "estimated_production_ton", "quality_status", "created_at"]].copy()
display["target_period"] = display["target_period"].dt.to_period("M").map(format_period)
display["estimated_production_ton"] = display["estimated_production_ton"].round(2)
display["created_at"] = display["created_at"].dt.strftime("%d-%m-%Y %H:%M")
display = display.rename(columns={
    "kabupaten": "Kabupaten", "target_period": "Periode",
    "estimated_production_ton": "Prediksi Produksi (ton)", "quality_status": "Status Data",
    "created_at": "Dibuat",
})
st.dataframe(display, hide_index=True, width="stretch")

st.subheader("Buka hasil")
labels = {
    row["id"]: f'{row["kabupaten"]} · {format_period(row["target_period"])} · {format_ton(row["estimated_production_ton"], 2)}'
    for _, row in filtered.iterrows()
}
selected_id = st.selectbox("Pilih hasil", filtered["id"].tolist(), format_func=labels.get, label_visibility="collapsed")
record = get_prediction(engine, selected_id)
period = pd.Period(record["target_period"], freq="M")

st.markdown(
    f"""
    <section class="padi-result">
      <div class="padi-muted">{record['kabupaten']} · {format_period(period)}</div>
      <div class="value">{format_ton(record['estimated_production_ton'], 2)}</div>
      <div class="padi-muted">Prediksi produksi yang tersimpan</div>
    </section>
    """,
    unsafe_allow_html=True,
)

support = index_history[
    (index_history["Kabupaten"] == record["kabupaten"])
    & index_history["Period"].isin([period - 2, period - 1, period])
].copy()
report_record = dict(record)
report_record["index_history"] = support

download_data = pd.DataFrame([{
    "Kabupaten": record["kabupaten"], "Periode": str(period),
    "Prediksi Produksi (ton)": round(record["estimated_production_ton"], 2), "Status Data": "Lengkap",
}])
d1, d2 = st.columns(2)
d1.download_button(
    "Unduh hasil CSV", download_data.to_csv(index=False).encode("utf-8"),
    file_name=f"hasil_{record['kabupaten'].lower()}_{period}.csv", mime="text/csv", width="stretch",
)
d2.download_button(
    "Unduh laporan PDF", build_prediction_pdf(report_record),
    file_name=f"laporan_{record['kabupaten'].lower()}_{period}.pdf", mime="application/pdf", width="stretch",
)
