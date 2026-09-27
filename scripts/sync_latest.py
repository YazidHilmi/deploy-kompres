"""Sinkronkan bulan penuh terakhir untuk semua kabupaten; entrypoint scheduler."""

import pandas as pd

from scripts.sync_gee import load_settings
from src.database import create_database_engine, initialize_database
from src.gee_client import initialize_earth_engine
from src.schemas import SUPPORTED_REGIONS
from src.sync_service import build_sync_plan, sync_one


def latest_complete_period(now=None):
    timestamp = pd.Timestamp.now(tz="Asia/Jakarta") if now is None else pd.Timestamp(now)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert("Asia/Jakarta").tz_localize(None)
    return timestamp.to_period("M") - 1


def main():
    target = latest_complete_period()
    settings = load_settings()
    engine = create_database_engine(settings["DATABASE_URL"])
    initialize_database(engine)
    initialize_earth_engine(
        settings["GEE_PROJECT_ID"], service_account=settings["GEE_SERVICE_ACCOUNT"],
        private_key=settings["GEE_PRIVATE_KEY"], service_account_json=settings["GEE_SERVICE_ACCOUNT_JSON"],
    )
    plan = build_sync_plan(engine, SUPPORTED_REGIONS, target, target, skip_existing=True)
    print(f"Bulan target: {target}; tugas: {len(plan)}", flush=True)
    failures = []
    for index, (region, period) in enumerate(plan, 1):
        try:
            result = sync_one(engine, region, period)
            print(f"[{index}/{len(plan)}] OK {region} {period}: {result['Jumlah Citra']} citra", flush=True)
        except Exception as error:
            failures.append((region, period, str(error)))
            print(f"[{index}/{len(plan)}] ERROR {region} {period}: {error}", flush=True)
    engine.dispose()
    if failures:
        raise SystemExit(f"Sinkronisasi selesai dengan {len(failures)} kegagalan.")


if __name__ == "__main__":
    main()
