import pandas as pd

from src.database import create_database_engine, initialize_database, upsert_monthly_index
from src.sync_service import build_sync_plan, month_range


def test_month_range_is_inclusive():
    assert month_range("2026-06", "2026-08") == [
        pd.Period("2026-06"), pd.Period("2026-07"), pd.Period("2026-08"),
    ]


def test_sync_plan_skips_existing_period(tmp_path):
    engine = create_database_engine(f"sqlite:///{(tmp_path / 'sync.db').as_posix()}")
    initialize_database(engine)
    upsert_monthly_index(
        engine, kabupaten="Tuban", period="2026-07", ndvi_mean=0.5,
        evi_mean=0.3, savi_mean=0.3, image_count=10, source="test",
    )
    plan = build_sync_plan(engine, ["Tuban"], "2026-06", "2026-08", skip_existing=True)
    assert plan == [("Tuban", pd.Period("2026-06")), ("Tuban", pd.Period("2026-08"))]
