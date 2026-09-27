import json

from src.gee_client import find_spatial_file


def test_spatial_file_prefers_sawah_geojson(tmp_path):
    folder = tmp_path / "ngawi"
    folder.mkdir()
    (folder / "BATAS_NGAWI.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": []}))
    sawah = folder / "SAWAH_NGAWI.geojson"
    sawah.write_text(json.dumps({"type": "FeatureCollection", "features": []}))
    assert find_spatial_file("Ngawi", tmp_path) == sawah
