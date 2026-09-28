"""Peta perbandingan prediksi dan indeks vegetasi."""

from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.app_services import get_engine, get_secret, load_index_history
from src.config import SPATIAL_DIR
from src.database import list_predictions
from src.gee_client import get_index_samples, get_index_tile_url, initialize_earth_engine
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

geojson = load_region_geojson()
if not geojson["features"]:
    st.error("Batas administrasi WGS84 belum tersedia untuk peta.")
    st.stop()

if indicator != "Prediksi Produksi":
    filter_col1, filter_col2 = st.columns(2)
    selected_region = filter_col1.selectbox("Kabupaten", SUPPORTED_REGIONS)
    region_periods = sorted(history.loc[history["Kabupaten"] == selected_region, "Period"].unique())
    selected_period = filter_col2.selectbox("Periode", list(reversed(region_periods)), format_func=format_period)
    st.caption(
        "Layer menampilkan variasi piksel indeks pada area sawah berdasarkan komposit citra Sentinel-2, bukan satu warna rata-rata kabupaten."
    )

    if st.button("Tampilkan layer indeks", type="primary", width="stretch"):
        project_id = get_secret("GEE_PROJECT_ID")
        if not project_id:
            st.error("Konfigurasi Google Earth Engine belum tersedia.")
        else:
            try:
                with st.spinner("Menyiapkan komposit citra dan layer peta..."):
                    initialize_earth_engine(
                        project_id=project_id, service_account=get_secret("GEE_SERVICE_ACCOUNT"),
                        private_key=get_secret("GEE_PRIVATE_KEY"),
                        service_account_json=get_secret("GEE_SERVICE_ACCOUNT_JSON"),
                    )
                    try:
                        tile_url, image_count = get_index_tile_url(selected_region, selected_period, indicator)
                        layer_data = {"mode": "raster", "tile_url": tile_url}
                    except Exception as tile_error:
                        if "earthengine.maps.create" not in str(tile_error):
                            raise
                        samples, image_count = get_index_samples(selected_region, selected_period, indicator)
                        layer_data = {"mode": "samples", "samples": samples}
                    st.session_state["gee_index_layer"] = {
                        "region": selected_region, "period": str(selected_period), "index": indicator,
                        "image_count": image_count, **layer_data,
                    }
            except Exception as error:
                st.error(f"Layer indeks belum dapat dimuat: {error}")

    layer = st.session_state.get("gee_index_layer")
    if layer and (layer["region"], layer["period"], layer["index"]) == (
        selected_region, str(selected_period), indicator,
    ):
        feature = next(item for item in geojson["features"] if item["id"] == selected_region)

        def points(value):
            if isinstance(value, (list, tuple)) and len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
                yield value
            elif isinstance(value, (list, tuple)):
                for child in value:
                    yield from points(child)

        coordinates = list(points(feature["geometry"]["coordinates"]))
        longitudes, latitudes = [item[0] for item in coordinates], [item[1] for item in coordinates]
        center = {"lon": (min(longitudes) + max(longitudes)) / 2, "lat": (min(latitudes) + max(latitudes)) / 2}
        colorscale = [[0, "#8c510a"], [.25, "#d8b365"], [.45, "#f6e8c3"], [.65, "#a6dba0"], [.82, "#5aae61"], [1, "#1b7837"]]
        if layer["mode"] == "raster":
            figure = go.Figure(go.Scattermap(
                lat=[center["lat"], center["lat"]], lon=[center["lon"], center["lon"]],
                mode="markers", marker={
                    "size": 0, "opacity": 0, "color": [-0.1, 0.8], "cmin": -0.1, "cmax": 0.8,
                    "colorscale": colorscale, "showscale": True,
                    "colorbar": {"title": indicator, "thickness": 14},
                }, hoverinfo="skip",
            ))
            map_layers = [{"sourcetype": "raster", "source": [layer["tile_url"]], "opacity": 0.82}]
        else:
            sample_frame = pd.DataFrame(layer["samples"])
            figure = go.Figure(go.Scattermap(
                lat=sample_frame["lat"], lon=sample_frame["lon"], mode="markers",
                marker={
                    "size": 8, "opacity": .8, "color": sample_frame["value"],
                    "cmin": -0.1, "cmax": .8, "colorscale": colorscale, "showscale": True,
                    "colorbar": {"title": indicator, "thickness": 14},
                },
                text=sample_frame["value"].map(lambda value: f"{indicator}: {value:.3f}"),
                hoverinfo="text",
            ))
            map_layers = []
        figure.update_layout(
            map={
                "style": "carto-positron", "center": center, "zoom": 8.2,
                "layers": map_layers,
            },
            margin={"l": 0, "r": 0, "t": 10, "b": 0}, height=590,
        )
        st.plotly_chart(figure, width="stretch")
        st.caption(
            f'{indicator} · {selected_region} · {format_period(selected_period)} · komposit {layer["image_count"]} citra. '
            "Cokelat/kuning menunjukkan nilai lebih rendah dan hijau menunjukkan nilai lebih tinggi."
        )
    else:
        st.info("Pilih wilayah dan periode, lalu tampilkan layer untuk memuat visualisasi indeks dari GEE.")
    st.stop()

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
