import pandas as pd

from src.database import (
    create_database_engine,
    get_prediction,
    initialize_database,
    list_predictions,
    save_prediction,
    seed_monthly_indices,
)
from src.features import prepare_index_history
from src.reports import build_prediction_pdf


def test_prediction_history_and_pdf(tmp_path):
    engine = create_database_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    initialize_database(engine)
    history = prepare_index_history(pd.DataFrame({
        "Kabupaten": ["Ngawi"], "Tahun": [2024], "Bulan": [1],
        "tanggal": ["2024-01-01"],
        "NDVI_mean": [0.6], "EVI_mean": [0.4], "SAVI_mean": [0.5],
    }))
    assert seed_monthly_indices(engine, history) == 1
    assert seed_monthly_indices(engine, history) == 0

    prediction_id = save_prediction(
        engine, kabupaten="Ngawi", target_period=pd.Period("2024-01", freq="M"),
        estimated_production_ton=12345.67, model_version="test-model",
        index_source="test.csv", input_features={"NDVI_mean": 0.6}, processing_seconds=1.2,
    )
    assert len(list_predictions(engine)) == 1
    assert len(list_predictions(engine, "Ngawi")) == 1
    assert list_predictions(engine, "Tuban").empty

    record = get_prediction(engine, prediction_id)
    assert record["estimated_production_ton"] == 12345.67
    assert record["input_features"] == {"NDVI_mean": 0.6}
    assert build_prediction_pdf(record).startswith(b"%PDF")
