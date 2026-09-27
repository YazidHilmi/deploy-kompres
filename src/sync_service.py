"""Orkestrasi sinkronisasi indeks GEE ke database."""

from __future__ import annotations

import pandas as pd

from src.config import SPATIAL_DIR
from src.database import existing_index_periods, upsert_monthly_index
from src.gee_client import fetch_monthly_indices


def month_range(start, end) -> list[pd.Period]:
    start_period, end_period = pd.Period(start, freq="M"), pd.Period(end, freq="M")
    if start_period > end_period:
        raise ValueError("Bulan awal tidak boleh setelah bulan akhir.")
    return list(pd.period_range(start_period, end_period, freq="M"))


def build_sync_plan(engine, regions, start, end, skip_existing=True):
    existing = existing_index_periods(engine) if skip_existing else set()
    return [
        (region, period)
        for region in regions
        for period in month_range(start, end)
        if (region, period) not in existing
    ]


def sync_one(engine, region: str, period: pd.Period) -> dict:
    values = fetch_monthly_indices(region, period, SPATIAL_DIR)
    action = upsert_monthly_index(
        engine, kabupaten=values["Kabupaten"], period=values["Period"],
        ndvi_mean=values["NDVI_mean"], evi_mean=values["EVI_mean"],
        savi_mean=values["SAVI_mean"], image_count=values["image_count"],
        source=values["source"], quality_status=values["quality_status"],
    )
    return {
        "Kabupaten": region, "Periode": str(period), "Status": action,
        "Jumlah Citra": values["image_count"], "NDVI": values["NDVI_mean"],
        "EVI": values["EVI_mean"], "SAVI": values["SAVI_mean"], "Error": "",
    }
