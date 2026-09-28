"""Dashboard utama produk."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app_services import get_engine, load_index_history
from src.database import list_predictions
from src.schemas import SUPPORTED_REGIONS
from src.ui import apply_theme, format_period, format_ton, page_header


def _latest_unique_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.copy()
    result["target_period"] = pd.to_datetime(result["target_period"])
    result["created_at"] = pd.to_datetime(result["created_at"])
    return result.sort_values("created_at").drop_duplicates(
        ["kabupaten", "target_period"], keep="last"
    )


def render_dashboard() -> None:
    apply_theme()
    page_header(
        "Pantau produksi padi dalam satu tampilan",
        "Lihat prediksi tersimpan, perkembangan produksi, dan tren vegetasi dari citra Sentinel-2 pada lima kabupaten sentra padi Jawa Timur.",
        "Padi Casting",
    )

    engine = get_engine()
    history = load_index_history()
    predictions = _latest_unique_predictions(list_predictions(engine))

    action_col, info_col = st.columns([1, 2.2], vertical_alignment="center")
    with action_col:
        if st.button("Buat prediksi baru", type="primary", width="stretch"):
            st.switch_page("pages/1_Prediksi_Produksi.py")
    with info_col:
        latest_data = history["Period"].max()
        st.markdown(
            f'<span class="padi-badge">Data satelit tersedia hingga {format_period(latest_data)}</span>',
            unsafe_allow_html=True,
        )

    st.subheader("Ringkasan platform")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kabupaten dipantau", len(SUPPORTED_REGIONS))
    m2.metric("Bulan observasi", history["Period"].nunique())
    m3.metric("Prediksi tersimpan", len(predictions))
    if predictions.empty:
        m4.metric("Prediksi terbaru", "Belum tersedia")
    else:
        newest = predictions.sort_values("created_at").iloc[-1]
        m4.metric("Prediksi terbaru", format_ton(newest["estimated_production_ton"]))

    st.subheader("Prediksi produksi tersimpan")
    if predictions.empty:
        st.info("Belum ada prediksi tersimpan. Mulai dari halaman Prediksi Produksi.")
    else:
        region_options = ["Semua", *SUPPORTED_REGIONS]
        selected_region = st.selectbox("Wilayah pada grafik produksi", region_options, label_visibility="collapsed")
        production = predictions.copy()
        if selected_region != "Semua":
            production = production[production["kabupaten"] == selected_region]
        production["Periode"] = production["target_period"].dt.strftime("%Y-%m")
        production = production.sort_values("target_period")
        figure = px.line(
            production, x="Periode", y="estimated_production_ton", color="kabupaten",
            markers=True, labels={"estimated_production_ton": "Prediksi produksi (ton)", "kabupaten": "Kabupaten"},
            color_discrete_sequence=["#1f6b45", "#4f8f65", "#d79a35", "#5a7894", "#856b8f"],
        )
        figure.update_layout(margin=dict(l=10, r=10, t=20, b=10), legend_title_text="Kabupaten")
        st.plotly_chart(figure, width="stretch")

        latest_by_region = production.sort_values("target_period").groupby("kabupaten", as_index=False).tail(1)
        latest_by_region = latest_by_region.rename(columns={
            "kabupaten": "Kabupaten", "Periode": "Periode",
            "estimated_production_ton": "Prediksi Produksi (ton)",
        })
        latest_by_region["Prediksi Produksi (ton)"] = latest_by_region["Prediksi Produksi (ton)"].round(2)
        st.dataframe(
            latest_by_region[["Kabupaten", "Periode", "Prediksi Produksi (ton)"]],
            hide_index=True, width="stretch",
        )

    st.subheader("Tren vegetasi")
    st.caption("Data observasi Sentinel-2. Nilai indeks bukan hasil prediksi model.")
    filter_col1, filter_col2 = st.columns([2, 1])
    vegetation_region = filter_col1.selectbox("Kabupaten", SUPPORTED_REGIONS, key="dashboard_vegetation_region")
    month_range = filter_col2.selectbox("Rentang", [3, 6, 12], index=2, format_func=lambda value: f"{value} bulan")

    vegetation = history[history["Kabupaten"] == vegetation_region].sort_values("Period").tail(month_range).copy()
    vegetation["Periode"] = vegetation["Period"].astype(str)
    latest = vegetation.iloc[-1]
    previous = vegetation.iloc[-2] if len(vegetation) > 1 else latest
    c1, c2, c3 = st.columns(3)
    for column, label, container in (
        ("NDVI_mean", "NDVI terbaru", c1), ("EVI_mean", "EVI terbaru", c2), ("SAVI_mean", "SAVI terbaru", c3),
    ):
        container.metric(label, f"{latest[column]:.3f}", delta=f"{latest[column] - previous[column]:+.3f} dari bulan sebelumnya")

    long_vegetation = vegetation.melt(
        id_vars="Periode", value_vars=["NDVI_mean", "EVI_mean", "SAVI_mean"],
        var_name="Indeks", value_name="Nilai",
    )
    long_vegetation["Indeks"] = long_vegetation["Indeks"].str.replace("_mean", "", regex=False)
    veg_figure = px.line(
        long_vegetation, x="Periode", y="Nilai", color="Indeks", markers=True,
        color_discrete_map={"NDVI": "#1f6b45", "EVI": "#d79a35", "SAVI": "#5a7894"},
    )
    veg_figure.update_layout(margin=dict(l=10, r=10, t=20, b=10), legend_title_text="Indeks")
    st.plotly_chart(veg_figure, width="stretch")

    st.caption(
        "Dashboard menampilkan hasil yang sudah tersimpan. Jalankan prediksi baru untuk menambahkan wilayah atau periode ke ringkasan produksi."
    )
