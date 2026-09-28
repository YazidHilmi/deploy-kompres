"""Autentikasi dan ekstraksi indeks Sentinel-2 melalui Google Earth Engine."""

from __future__ import annotations

import json
from pathlib import Path

import ee
import pandas as pd

from src.config import SPATIAL_DIR


SENTINEL_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"


def initialize_earth_engine(project_id: str, service_account: str | None = None,
                            private_key: str | None = None, service_account_json: str | None = None) -> None:
    if not project_id:
        raise ValueError("GEE_PROJECT_ID belum diisi.")

    if service_account_json:
        credentials = ee.ServiceAccountCredentials(key_data=service_account_json)
        ee.Initialize(credentials=credentials, project=project_id)
    elif service_account and private_key:
        key_data = json.dumps({
            "type": "service_account", "client_email": service_account,
            "private_key": private_key.replace("\\n", "\n"),
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        credentials = ee.ServiceAccountCredentials(email=service_account, key_data=key_data)
        ee.Initialize(credentials=credentials, project=project_id)
    else:
        ee.Initialize(project=project_id)


def find_spatial_file(kabupaten: str, spatial_dir: Path = SPATIAL_DIR) -> Path:
    folder = Path(spatial_dir) / kabupaten.lower()
    candidates = list(folder.glob("*.geojson")) + list(folder.glob("*.json"))
    if not candidates:
        raise FileNotFoundError(f"GeoJSON untuk {kabupaten} belum ada di {folder}.")
    sawah = [path for path in candidates if "sawah" in path.name.lower()]
    preferred = sawah or candidates
    wgs84 = [path for path in preferred if "wgs84" in path.name.lower()]
    return sorted(wgs84 or preferred)[0]


def load_ee_geometry(kabupaten: str, spatial_dir: Path = SPATIAL_DIR):
    path = find_spatial_file(kabupaten, spatial_dir)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("type") == "FeatureCollection":
        geometries = [
            feature.get("geometry") for feature in payload.get("features", [])
            if feature.get("geometry", {}).get("type") in {"Polygon", "MultiPolygon"}
        ]
        if not geometries:
            raise ValueError(f"GeoJSON {path.name} tidak memiliki feature.")
        return ee.FeatureCollection([ee.Feature(ee.Geometry(item)) for item in geometries]).geometry(), path
    if payload.get("type") == "Feature":
        payload = payload["geometry"]
    return ee.Geometry(payload), path


def _mask_and_add_indices(image):
    scl = image.select("SCL")
    clear = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
    reflectance = image.select(["B2", "B4", "B8"]).multiply(0.0001)
    blue, red, nir = reflectance.select("B2"), reflectance.select("B4"), reflectance.select("B8")
    ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
    evi = nir.subtract(red).multiply(2.5).divide(
        nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
    ).rename("EVI")
    savi = nir.subtract(red).multiply(1.5).divide(nir.add(red).add(0.5)).rename("SAVI")
    return image.addBands([ndvi, evi, savi]).updateMask(clear)


def fetch_monthly_indices(kabupaten: str, period, spatial_dir: Path = SPATIAL_DIR) -> dict:
    image, geometry, image_count, path = build_monthly_index_image(kabupaten, period, spatial_dir)
    values = image.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=geometry, scale=10, bestEffort=True, maxPixels=1_000_000_000,
    ).getInfo()
    if any(values.get(key) is None for key in ("NDVI", "EVI", "SAVI")):
        raise ValueError("GEE tidak menghasilkan nilai indeks yang lengkap setelah cloud masking.")
    return {
        "Kabupaten": kabupaten, "Period": pd.Period(period, freq="M"),
        "NDVI_mean": float(values["NDVI"]), "EVI_mean": float(values["EVI"]),
        "SAVI_mean": float(values["SAVI"]), "image_count": image_count,
        "source": f"GEE:{SENTINEL_COLLECTION}:{path.name}", "quality_status": "valid",
    }


def build_monthly_index_image(kabupaten: str, period, spatial_dir: Path = SPATIAL_DIR):
    period = pd.Period(period, freq="M")
    start = period.to_timestamp().strftime("%Y-%m-%d")
    end = (period + 1).to_timestamp().strftime("%Y-%m-%d")
    geometry, path = load_ee_geometry(kabupaten, spatial_dir)
    collection = (
        ee.ImageCollection(SENTINEL_COLLECTION).filterBounds(geometry).filterDate(start, end)
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 80)).map(_mask_and_add_indices)
    )
    image_count = int(collection.size().getInfo())
    if image_count == 0:
        raise ValueError(f"Tidak ada citra Sentinel-2 untuk {kabupaten} pada {period}.")
    image = collection.median().select(["NDVI", "EVI", "SAVI"]).clip(geometry)
    return image, geometry, image_count, path


def get_index_tile_url(kabupaten: str, period, index_name: str,
                       spatial_dir: Path = SPATIAL_DIR) -> tuple[str, int]:
    """Buat URL tile sementara untuk visualisasi piksel indeks dari GEE."""
    index_name = index_name.upper()
    if index_name not in {"NDVI", "EVI", "SAVI"}:
        raise ValueError(f"Indeks tidak didukung: {index_name}")
    image, _, image_count, _ = build_monthly_index_image(kabupaten, period, spatial_dir)
    visualization = {
        "min": -0.1, "max": 0.8,
        "palette": ["8c510a", "d8b365", "f6e8c3", "a6dba0", "5aae61", "1b7837"],
    }
    map_id = image.select(index_name).getMapId(visualization)
    return map_id["tile_fetcher"].url_format, image_count


def get_index_samples(kabupaten: str, period, index_name: str, max_points: int = 1600,
                      spatial_dir: Path = SPATIAL_DIR) -> tuple[list[dict], int]:
    """Ambil sampel piksel untuk fallback visual tanpa izin maps.create."""
    index_name = index_name.upper()
    if index_name not in {"NDVI", "EVI", "SAVI"}:
        raise ValueError(f"Indeks tidak didukung: {index_name}")
    image, geometry, image_count, _ = build_monthly_index_image(kabupaten, period, spatial_dir)
    payload = image.select(index_name).sample(
        region=geometry, scale=100, numPixels=max_points, seed=42,
        dropNulls=True, geometries=True, tileScale=4,
    ).getInfo()
    samples = []
    for feature in payload.get("features", []):
        coordinates = feature.get("geometry", {}).get("coordinates", [])
        value = feature.get("properties", {}).get(index_name)
        if len(coordinates) >= 2 and value is not None:
            samples.append({"lon": float(coordinates[0]), "lat": float(coordinates[1]), "value": float(value)})
    if not samples:
        raise ValueError("GEE tidak menghasilkan sampel piksel indeks pada area sawah.")
    return samples, image_count
