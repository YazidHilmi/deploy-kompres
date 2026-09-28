"""Konversi GeoJSON RBI ke WGS84 dan buang atribut yang tidak diperlukan GEE."""

import json
from pathlib import Path

from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import mapping, shape


ROOT = Path(__file__).resolve().parents[1] / "data" / "spatial"
TRANSFORMER = Transformer.from_crs("EPSG:9518", "EPSG:4326", always_xy=True)


def transform_coordinates(value):
    if value and isinstance(value[0], (int, float)):
        longitude, latitude = TRANSFORMER.transform(value[0], value[1])
        return [round(longitude, 7), round(latitude, 7)]
    return [transform_coordinates(item) for item in value]


def transform_geometry(geometry):
    return {
        "type": geometry["type"],
        "coordinates": transform_coordinates(geometry["coordinates"]),
    }


def target_admin_geometry(folder: Path):
    payload = json.loads((folder / "batas_administrasi.geojson").read_text(encoding="utf-8"))
    region = folder.name.casefold()
    matches = []
    for feature in payload.get("features", []):
        properties = feature.get("properties", {})
        name = str(properties.get("WADMKK") or properties.get("NAMOBJ") or "").casefold()
        geometry = feature.get("geometry")
        if name == region and geometry and geometry.get("type") in {"Polygon", "MultiPolygon"}:
            matches.append(make_valid(shape(transform_geometry(geometry))))
    if len(matches) != 1:
        raise ValueError(f"{folder.name}: batas target ditemukan {len(matches)}, seharusnya 1")
    return matches[0]


def convert_file(source: Path, target: Path, boundary) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    features = []
    is_boundary = source.name == "batas_administrasi.geojson"
    region = source.parent.name
    for feature in payload.get("features", []):
        geometry = feature.get("geometry")
        if not geometry or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            continue
        if is_boundary:
            properties = feature.get("properties", {})
            name = str(properties.get("WADMKK") or properties.get("NAMOBJ") or "")
            if name.casefold() != region.casefold():
                continue
            cleaned = boundary
        else:
            cleaned = make_valid(shape(transform_geometry(geometry))).intersection(boundary)
        if cleaned.is_empty:
            continue
        if cleaned.geom_type not in {"Polygon", "MultiPolygon"}:
            polygon_parts = [
                part for part in getattr(cleaned, "geoms", [])
                if part.geom_type in {"Polygon", "MultiPolygon"}
            ]
            if not polygon_parts:
                continue
            from shapely.ops import unary_union
            cleaned = unary_union(polygon_parts)
        features.append({
            "type": "Feature", "properties": {"Kabupaten": region.title()},
            "geometry": mapping(cleaned),
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
        boundary = target_admin_geometry(folder)
        for name in ("sawah", "batas_administrasi"):
            source = folder / f"{name}.geojson"
            if source.exists():
                convert_file(source, folder / f"{name}_wgs84.geojson", boundary)
