"""Analisis beberapa wilayah atau periode dalam satu proses."""

from __future__ import annotations

import time

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app_services import get_engine, get_tabpfn_model, load_index_history
from src.database import save_prediction
from src.features import build_feature_row, get_available_target_periods
from src.model import predict_production
from src.schemas import SUPPORTED_REGIONS
from src.ui import apply_theme, format_period, page_header


apply_theme()
page_header(
    "Analisis dan perbandingan",
    "Bandingkan prediksi produksi antarwilayah atau ikuti perkembangan satu wilayah pada beberapa periode.",
    "Analisis Produksi",
)

engine, history = get_engine(), load_index_history()
mode = st.radio(
    "Jenis analisis", ["Beberapa kabupaten pada satu periode", "Satu kabupaten pada beberapa periode"],
    horizontal=True,
)

jobs = []
if mode == "Beberapa kabupaten pada satu periode":
    regions = st.multiselect("Kabupaten", SUPPORTED_REGIONS, default=SUPPORTED_REGIONS)
    period_sets = [set(get_available_target_periods(history, region)) for region in regions]
    common_periods = sorted(set.intersection(*period_sets)) if period_sets else []
    if common_periods:
        selected_period = st.selectbox("Periode", list(reversed(common_periods)), format_func=format_period)
        jobs = [(region, selected_period) for region in regions]
    else:
        st.info("Pilih wilayah yang memiliki periode data yang sama.")
else:
    region = st.selectbox("Kabupaten", SUPPORTED_REGIONS)
    available = get_available_target_periods(history, region)
    if available:
        default_periods = list(reversed(available))[: min(6, len(available))]
        periods = st.multiselect("Periode", list(reversed(available)), default=default_periods, format_func=format_period)
        jobs = [(region, period) for period in sorted(periods)]

st.caption(f"{len(jobs)} prediksi akan diproses dalam satu analisis.")
if st.button("Jalankan analisis", type="primary", width="stretch", disabled=not jobs):
    try:
        feature_frames, metadata = [], []
        for region, period in jobs:
            feature_frames.append(build_feature_row(history, region, period))
            metadata.append((region, period))
        features = pd.concat(feature_frames, ignore_index=True)
        with st.status("Menjalankan analisis...", expanded=True) as status:
            model, _ = get_tabpfn_model()
            started_at = time.perf_counter()
            values = predict_production(model, features)
            elapsed = time.perf_counter() - started_at
            results = []
            for row_index, ((region, period), value) in enumerate(zip(metadata, values)):
                prediction_id = save_prediction(
                    engine, kabupaten=region, target_period=period,
                    estimated_production_ton=float(value), model_version="TabPFN Client 3.5",
                    index_source="Sentinel-2 / Google Earth Engine",
                    input_features=features.iloc[row_index].to_dict(),
                    processing_seconds=elapsed / len(metadata),
                )
                results.append({
                    "Kabupaten": region, "Period": period, "Periode": format_period(period),
                    "Prediksi Produksi (ton)": float(value), "id": prediction_id,
                })
            st.session_state["batch_analysis_results"] = pd.DataFrame(results)
            status.update(label="Analisis selesai", state="complete", expanded=False)
    except Exception as error:
        st.error(f"Analisis belum berhasil diproses: {error}")

results = st.session_state.get("batch_analysis_results")
if isinstance(results, pd.DataFrame) and not results.empty:
    st.divider()
    st.subheader("Hasil analisis")
    total, average, maximum = st.columns(3)
    total.metric("Total prediksi", f'{results["Prediksi Produksi (ton)"].sum():,.0f} ton')
    average.metric("Rata-rata", f'{results["Prediksi Produksi (ton)"].mean():,.0f} ton')
    top = results.loc[results["Prediksi Produksi (ton)"].idxmax()]
    maximum.metric("Hasil tertinggi", top["Kabupaten"], f'{top["Prediksi Produksi (ton)"]:,.0f} ton')

    if results["Kabupaten"].nunique() > 1:
        figure = px.bar(
            results, x="Kabupaten", y="Prediksi Produksi (ton)", color="Kabupaten",
            color_discrete_sequence=["#1f6b45", "#4f8f65", "#d79a35", "#5a7894", "#856b8f"],
        )
        figure.update_layout(showlegend=False, margin=dict(l=10, r=10, t=20, b=10))
    else:
        figure = px.line(
            results.sort_values("Period"), x="Periode", y="Prediksi Produksi (ton)", markers=True,
            color_discrete_sequence=["#1f6b45"],
        )
        figure.update_layout(margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(figure, width="stretch")
    display = results[["Kabupaten", "Periode", "Prediksi Produksi (ton)"]].copy()
    display["Prediksi Produksi (ton)"] = display["Prediksi Produksi (ton)"].round(2)
    st.dataframe(display, hide_index=True, width="stretch")
    st.download_button(
        "Unduh tabel analisis", display.to_csv(index=False).encode("utf-8"),
        file_name="analisis_prediksi_produksi.csv", mime="text/csv", width="stretch",
    )
    st.success("Seluruh hasil analisis telah disimpan ke riwayat.")
