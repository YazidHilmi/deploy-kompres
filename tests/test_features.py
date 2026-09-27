import json

import numpy as np
import pandas as pd

from src.config import HISTORICAL_INDEX_PATH, VALIDATION_REFERENCE_PATH
from src.features import build_feature_row, prepare_index_history
from src.schemas import FEATURE_COLUMNS


def test_feature_builder_matches_validation_reference():
    history = prepare_index_history(pd.read_csv(HISTORICAL_INDEX_PATH))

    with open(VALIDATION_REFERENCE_PATH, encoding="utf-8") as file:
        reference = json.load(file)

    period = f"{reference['tahun']}-{reference['bulan']:02d}"
    features = build_feature_row(history, reference["kabupaten"], period)
    expected = np.array(
        [reference["fitur_final_values"][name] for name in FEATURE_COLUMNS],
        dtype=float,
    )

    assert features.shape == (1, 18)
    np.testing.assert_allclose(
        features.iloc[0].to_numpy(dtype=float), expected, rtol=1e-10, atol=1e-12
    )
