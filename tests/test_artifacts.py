from src.artifacts import load_training_artifacts
from src.schemas import FEATURE_COLUMNS


def test_training_artifacts_match_contract():
    artifacts = load_training_artifacts()

    assert artifacts["X_train"].shape == (290, 18)
    assert artifacts["y_train"].shape == (290,)
    assert list(artifacts["X_train"].columns) == FEATURE_COLUMNS
    assert artifacts["model_config"]["fitur_final"] == FEATURE_COLUMNS
    assert artifacts["best_params"]["n_estimators"] == 8
