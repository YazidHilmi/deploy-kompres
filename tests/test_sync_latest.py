import pandas as pd

from scripts.sync_latest import latest_complete_period


def test_latest_complete_period_uses_previous_month():
    assert latest_complete_period("2026-09-28") == pd.Period("2026-08")
    assert latest_complete_period("2026-01-02") == pd.Period("2025-12")
