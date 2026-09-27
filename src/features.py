import numpy as np
import pandas as pd

from src.schemas import FEATURE_COLUMNS, REGION_DUMMIES, SUPPORTED_REGIONS


REQUIRED_INDEX_COLUMNS = [
    "Kabupaten",
    "Tahun",
    "Bulan",
    "tanggal",
    "NDVI_mean",
    "EVI_mean",
    "SAVI_mean",
]


def prepare_index_history(frame):
    missing = [
        column
        for column in REQUIRED_INDEX_COLUMNS
        if column not in frame.columns
    ]

    if missing:
        raise ValueError(
            f"Kolom indeks tidak lengkap: {missing}"
        )

    result = frame.copy()
    result["tanggal"] = pd.to_datetime(result["tanggal"])
    result["Period"] = result["tanggal"].dt.to_period("M")

    for column in ["NDVI_mean", "EVI_mean", "SAVI_mean"]:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    result["EVI_mean"] = result["EVI_mean"].clip(-1, 1)
    result = result.sort_values(["Kabupaten", "Period"])
    result = result.reset_index(drop=True)

    if result[REQUIRED_INDEX_COLUMNS].isna().any().any():
        raise ValueError("Data indeks memiliki nilai kosong.")

    duplicates = result.duplicated(
        subset=["Kabupaten", "Period"]
    )

    if duplicates.any():
        raise ValueError(
            "Ditemukan kabupaten dan bulan yang duplikat."
        )

    return result


def get_available_target_periods(history, kabupaten):
    region_data = history[
        history["Kabupaten"] == kabupaten
    ]

    available = set(region_data["Period"])
    valid_targets = [
        period
        for period in sorted(available)
        if period - 1 in available and period - 2 in available
    ]

    return valid_targets


def build_feature_row(history, kabupaten, target_period):
    if kabupaten not in SUPPORTED_REGIONS:
        raise ValueError(
            f"Kabupaten tidak didukung: {kabupaten}"
        )

    target_period = pd.Period(target_period, freq="M")
    required_periods = [
        target_period - 2,
        target_period - 1,
        target_period,
    ]

    region_data = history[
        (history["Kabupaten"] == kabupaten)
        & (history["Period"].isin(required_periods))
    ].copy()

    region_data = region_data.set_index("Period").sort_index()

    missing_periods = [
        str(period)
        for period in required_periods
        if period not in region_data.index
    ]

    if missing_periods:
        raise ValueError(
            "Data indeks belum lengkap untuk bulan: "
            + ", ".join(missing_periods)
        )

    lag2 = region_data.loc[target_period - 2]
    lag1 = region_data.loc[target_period - 1]
    current = region_data.loc[target_period]

    month = target_period.month

    features = {
        "NDVI_mean": current["NDVI_mean"],
        "EVI_mean": current["EVI_mean"],
        "SAVI_mean": current["SAVI_mean"],
        "Bulan_sin": np.sin(2 * np.pi * month / 12),
        "Bulan_cos": np.cos(2 * np.pi * month / 12),
        **REGION_DUMMIES[kabupaten],
        "NDVI_mean_delta1": (
            current["NDVI_mean"] - lag1["NDVI_mean"]
        ),
        "SAVI_mean_delta1": (
            current["SAVI_mean"] - lag1["SAVI_mean"]
        ),
        "NDVI_mean_lag2": lag2["NDVI_mean"],
        "SAVI_mean_lag1": lag1["SAVI_mean"],
        "NDVI_mean_lag1": lag1["NDVI_mean"],
        "SAVI_mean_lag2": lag2["SAVI_mean"],
        "NDVI_mean_roll3": np.mean([
            lag2["NDVI_mean"],
            lag1["NDVI_mean"],
            current["NDVI_mean"],
        ]),
        "SAVI_mean_roll3": np.mean([
            lag2["SAVI_mean"],
            lag1["SAVI_mean"],
            current["SAVI_mean"],
        ]),
        "EVI_mean_delta1": (
            current["EVI_mean"] - lag1["EVI_mean"]
        ),
    }

    X = pd.DataFrame([features], columns=FEATURE_COLUMNS)
    X = X.astype(float)

    validate_feature_frame(X)
    return X


def build_feature_batch(history, kabupaten, target_periods):
    rows = [
        build_feature_row(
            history=history,
            kabupaten=kabupaten,
            target_period=period,
        )
        for period in target_periods
    ]

    if not rows:
        raise ValueError("Tidak ada bulan yang dapat diproses.")

    result = pd.concat(rows, ignore_index=True)
    validate_feature_frame(result)

    return result


def validate_feature_frame(frame):
    if list(frame.columns) != FEATURE_COLUMNS:
        raise ValueError("Urutan feature frame tidak sesuai schema.")

    if frame.shape[1] != 18:
        raise ValueError(
            f"Feature frame harus 18 kolom, ditemukan {frame.shape[1]}."
        )

    if frame.isna().any().any():
        missing = frame.columns[frame.isna().any()].tolist()
        raise ValueError(
            f"Feature frame memiliki NaN: {missing}"
        )

    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError("Feature frame memiliki nilai non-finite.")