"""CLI sinkronisasi GEE; cocok dipanggil scheduler atau Cloud Run Job."""

import argparse
import json
import os
import tomllib
from pathlib import Path

from src.database import create_database_engine, initialize_database
from src.gee_client import initialize_earth_engine
from src.schemas import SUPPORTED_REGIONS
from src.sync_service import build_sync_plan, sync_one


def load_settings():
    path = Path(".streamlit/secrets.toml")
    file_values = tomllib.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return {key: os.getenv(key) or file_values.get(key) for key in (
        "DATABASE_URL", "GEE_PROJECT_ID", "GEE_SERVICE_ACCOUNT_JSON",
        "GEE_SERVICE_ACCOUNT", "GEE_PRIVATE_KEY",
    )}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="Bulan awal, contoh 2026-01")
    parser.add_argument("--end", required=True, help="Bulan akhir, contoh 2026-08")
    parser.add_argument("--regions", nargs="+", choices=SUPPORTED_REGIONS, default=SUPPORTED_REGIONS)
    parser.add_argument("--force", action="store_true", help="Perbarui juga data yang sudah ada")
    args = parser.parse_args()
    settings = load_settings()

    engine = create_database_engine(settings["DATABASE_URL"])
    initialize_database(engine)
    initialize_earth_engine(
        settings["GEE_PROJECT_ID"], service_account=settings["GEE_SERVICE_ACCOUNT"],
        private_key=settings["GEE_PRIVATE_KEY"], service_account_json=settings["GEE_SERVICE_ACCOUNT_JSON"],
    )
    plan = build_sync_plan(engine, args.regions, args.start, args.end, not args.force)
    print(f"Tugas yang akan dijalankan: {len(plan)}")
    failures = 0
    for index, (region, period) in enumerate(plan, 1):
        try:
            result = sync_one(engine, region, period)
            print(f"[{index}/{len(plan)}] {json.dumps(result, ensure_ascii=False)}", flush=True)
        except Exception as error:
            failures += 1
            print(f"[{index}/{len(plan)}] ERROR {region} {period}: {error}", flush=True)
    engine.dispose()
    if failures:
        raise SystemExit(f"Selesai dengan {failures} kegagalan.")


if __name__ == "__main__":
    main()
