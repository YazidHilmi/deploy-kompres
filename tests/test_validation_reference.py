import json
import os
import tomllib

import pandas as pd
import pytest

from src.artifacts import load_training_artifacts
from src.config import (
    HISTORICAL_INDEX_PATH,
    PROJECT_ROOT,
    VALIDATION_REFERENCE_PATH,
)
from src.features import build_feature_row, prepare_index_history
from src.model import fit_model, predict_production


def _read_token():
    token = os.getenv("TABPFN_TOKEN")
    if token:
        return token

    secret_path = PROJECT_ROOT / ".streamlit" / "secrets.toml"
    if not secret_path.exists():
        return None

    with open(secret_path, "rb") as file:
        return tomllib.load(file).get("TABPFN_TOKEN")


@pytest.mark.integration
def test_tabpfn_prediction_matches_reference():
    if os.getenv("RUN_TABPFN_INTEGRATION") != "1":
        pytest.skip("Set RUN_TABPFN_INTEGRATION=1 to call TabPFN Client.")

    token = _read_token()
    if not token:
        pytest.skip("TABPFN_TOKEN is not configured.")

    artifacts = load_training_artifacts()
    history = prepare_index_history(pd.read_csv(HISTORICAL_INDEX_PATH))

    with open(VALIDATION_REFERENCE_PATH, encoding="utf-8") as file:
        reference = json.load(file)

    period = f"{reference['tahun']}-{reference['bulan']:02d}"
    features = build_feature_row(history, reference["kabupaten"], period)
    model = fit_model(
        artifacts["X_train"],
        artifacts["y_train"],
        artifacts["best_params"],
        token,
    )
    prediction = predict_production(model, features)[0]

    assert prediction == pytest.approx(
        reference["prediksi_notebook"], rel=1e-4, abs=1.0
    )
