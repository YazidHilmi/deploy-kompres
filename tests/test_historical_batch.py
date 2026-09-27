import pandas as pd

from src.config import HISTORICAL_INDEX_PATH
from src.features import build_feature_batch, prepare_index_history
from src.schemas import FEATURE_COLUMNS


def test_build_five_month_historical_batch():
    history = prepare_index_history(pd.read_csv(HISTORICAL_INDEX_PATH))
    target_periods = pd.period_range("2024-08", "2024-12", freq="M")

    features = build_feature_batch(history, "Ngawi", target_periods)

    assert features.shape == (5, 18)
    assert list(features.columns) == FEATURE_COLUMNS
    assert not features.isna().any().any()
