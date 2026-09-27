import json

import joblib
import numpy as np
import pandas as pd

from src.config import (
    BEST_PARAMS_PATH,
    METADATA_PATH,
    MODEL_CONFIG_PATH,
    X_TRAIN_PATH,
    Y_TRAIN_PATH,
)

from src.schemas import FEATURE_COLUMNS


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_training_artifacts():
    X_train = pd.read_csv(X_TRAIN_PATH)
    y_train = pd.read_csv(Y_TRAIN_PATH)["Produksi_Ton"]
    best_params = joblib.load(BEST_PARAMS_PATH)
    model_config = load_json(MODEL_CONFIG_PATH)
    metadata = load_json(METADATA_PATH)

    validate_training_artifacts(
        X_train=X_train,
        y_train=y_train,
        model_config=model_config,
    )

    return {
        "X_train": X_train,
        "y_train": y_train,
        "best_params": best_params,
        "model_config": model_config,
        "metadata": metadata,
    }


def validate_training_artifacts(X_train, y_train, model_config):
    if list(X_train.columns) != FEATURE_COLUMNS:
        raise ValueError(
            "Urutan fitur X_train tidak sama dengan schema deployment."
        )

    if model_config["fitur_final"] != FEATURE_COLUMNS:
        raise ValueError(
            "Fitur dalam model_config.json tidak sama dengan schema."
        )

    if len(X_train) != len(y_train):
        raise ValueError(
            f"Jumlah X dan y berbeda: {len(X_train)} != {len(y_train)}"
        )

    if X_train.shape[1] != 18:
        raise ValueError(
            f"Model membutuhkan 18 fitur, ditemukan {X_train.shape[1]}."
        )

    if X_train.isna().any().any() or y_train.isna().any():
        raise ValueError("Reference training masih memiliki nilai kosong.")

    if not np.isfinite(X_train.to_numpy(dtype=float)).all():
        raise ValueError("Reference training memiliki nilai non-finite.")

    if not np.isfinite(y_train.to_numpy(dtype=float)).all():
        raise ValueError("Target training memiliki nilai non-finite.")