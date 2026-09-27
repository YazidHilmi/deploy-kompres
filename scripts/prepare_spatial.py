"""Konversi GeoJSON RBI ke WGS84 dan buang atribut yang tidak diperlukan GEE."""

import json
from pathlib import Path

from pyproj import Transformer


ROOT = Path(__file__).resolve().parents[1] / "data" / "spatial"
TRANSFORMER = Transformer.from_crs("EPSG:9518", "EPSG:4326", always_xy=True)


def transform_coordinates(value):
    if value and isinstance(value[0], (int, float)):
        longitude, latitude = TRANSFORMER.transform(value[0], value[1])
        return [round(longitude, 7), round(latitude, 7)]
    return [transform_coordinates(item) for item in value]


def convert_file(source: Path, target: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    features = []
    for feature in payload.get("features", []):
        geometry = feature.get("geometry")
        if not geometry or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            continue
        features.append({
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": geometry["type"],
                "coordinates": transform_coordinates(geometry["coordinates"]),
            },
        })
    result = {
        "type": "FeatureCollection",
        "name": target.stem,
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }
    target.write_text(json.dumps(result, separators=(",", ":")), encoding="utf-8")
    print(f"{source.name} -> {target.name}: {len(features)} features")


if __name__ == "__main__":
    for folder in sorted(path for path in ROOT.iterdir() if path.is_dir()):
        for name in ("sawah", "batas_administrasi"):
            source = folder / f"{name}.geojson"
            if source.exists():
                convert_file(source, folder / f"{name}_wgs84.geojson")
