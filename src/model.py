import numpy as np
import pandas as pd

from tabpfn_client import TabPFNRegressor, set_access_token

from src.schemas import FEATURE_COLUMNS


def fit_model(X_train, y_train, best_params, access_token):
    if not access_token:
        raise ValueError("TABPFN_TOKEN belum dikonfigurasi.")

    set_access_token(access_token)

    model = TabPFNRegressor(**best_params)
    model.fit(
        X_train.to_numpy(dtype=float),
        y_train.to_numpy(dtype=float),
    )

    return model


def predict_production(model, features):
    if list(features.columns) != FEATURE_COLUMNS:
        raise ValueError("Urutan fitur inference tidak sesuai schema.")

    prediction = model.predict(
        features.to_numpy(dtype=float)
    )

    prediction = np.asarray(prediction, dtype=float).reshape(-1)
    prediction = np.clip(prediction, 0, None)

    return prediction