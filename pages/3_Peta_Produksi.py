"""Peta perbandingan prediksi dan indeks vegetasi."""

from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app_services import get_engine, load_index_history
from src.config import SPATIAL_DIR
from src.database import list_predictions
from src.schemas import SUPPORTED_REGIONS
from src.ui import apply_theme, format_period, page_header


apply_theme()
page_header(
    "Peta produksi dan vegetasi",
    "Jelajahi perbandingan wilayah berdasarkan prediksi produksi tersimpan atau observasi indeks vegetasi.",
    "Eksplorasi Wilayah",
)


@st.cache_data
def load_region_geojson():
    features = []
    for region in SUPPORTED_REGIONS:
        path = SPATIAL_DIR / region.lower() / "batas_administrasi_wgs84.geojson"
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        polygons = []
        source_features = payload.get("features", []) if payload.get("type") == "FeatureCollection" else [payload]
        for feature in source_features:
            geometry = feature.get("geometry", feature)
            if geometry.get("type") == "Polygon":
                polygons.append(geometry["coordinates"])
            elif geometry.get("type") == "MultiPolygon":
                polygons.extend(geometry["coordinates"])
        if polygons:
            features.append({
                "type": "Feature", "id": region,
                "properties": {"Kabupaten": region},
                "geometry": {"type": "MultiPolygon", "coordinates": polygons},
            })
    return {"type": "FeatureCollection", "features": features}


history = load_index_history()
predictions = list_predictions(get_engine())
indicator = st.selectbox("Tampilkan pada peta", ["Prediksi Produksi", "NDVI", "EVI", "SAVI"])

if indicator == "Prediksi Produksi":
    if predictions.empty:
        st.info("Belum ada prediksi tersimpan untuk ditampilkan pada peta.")
        st.stop()
    predictions["Period"] = pd.to_datetime(predictions["target_period"]).dt.to_period("M")
    available_periods = sorted(predictions["Period"].unique())
    selected_period = st.selectbox("Periode", list(reversed(available_periods)), format_func=format_period)
    data = predictions[predictions["Period"] == selected_period].copy()
    data = data.sort_values("created_at").drop_duplicates("kabupaten", keep="last")
    data = data.rename(columns={"kabupaten": "Kabupaten", "estimated_production_ton": "Nilai"})
    unit, color_title = "ton", "Prediksi produksi"
else:
    available_periods = sorted(history["Period"].unique())
    selected_period = st.selectbox("Periode", list(reversed(available_periods)), format_func=format_period)
    column = f"{indicator}_mean"
    data = history[history["Period"] == selected_period][["Kabupaten", column]].copy()
    data = data.rename(columns={column: "Nilai"})
    unit, color_title = "indeks", indicator

geojson = load_region_geojson()
if not geojson["features"]:
    st.error("Batas administrasi WGS84 belum tersedia untuk peta.")
    st.stop()

figure = px.choropleth_map(
    data, geojson=geojson, locations="Kabupaten", featureidkey="id", color="Nilai",
    hover_name="Kabupaten", hover_data={"Nilai": ":,.3f"},
    color_continuous_scale=["#eef5f0", "#7db38d", "#1f6b45"],
    map_style="carto-positron", center={"lat": -7.55, "lon": 112.3}, zoom=6.2,
    opacity=0.72, labels={"Nilai": color_title},
)
figure.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=560)
st.plotly_chart(figure, width="stretch")
st.caption(f"{color_title} untuk {format_period(selected_period)}. Wilayah tanpa warna belum memiliki data pada periode ini.")

display = data.rename(columns={"Nilai": f"{color_title} ({unit})"}).sort_values(f"{color_title} ({unit})", ascending=False)
st.dataframe(display, hide_index=True, width="stretch")
