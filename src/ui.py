"""Komponen visual dan format yang dipakai seluruh halaman."""

from __future__ import annotations

import pandas as pd
import streamlit as st


MONTHS_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root { --padi-green:#1f6b45; --padi-ink:#17211b; --padi-soft:#f3f7f4; }
        .stApp { background: #f7f9f7; color: var(--padi-ink); }
        .block-container { max-width: 1240px; padding-top: 2.2rem; padding-bottom: 4rem; }
        h1, h2, h3 { letter-spacing: -.025em; color: var(--padi-ink); }
        h1 { font-size: clamp(2rem, 4vw, 3.2rem) !important; }
        [data-testid="stMetric"] { background:#fff; border:1px solid #e2e9e4; border-radius:16px; padding:18px; }
        [data-testid="stMetricLabel"] { color:#5e6c63; }
        [data-testid="stMetricValue"] { color:var(--padi-ink); font-weight:700; }
        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] { background:#fff; border:1px solid #e2e9e4; border-radius:16px; padding:8px; }
        .stButton > button, .stDownloadButton > button { border-radius:10px; min-height:44px; font-weight:600; }
        .stButton > button[kind="primary"] { background:var(--padi-green); border-color:var(--padi-green); }
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div { border-radius:10px; }
        .padi-hero { background:linear-gradient(130deg,#173f2c 0%,#2f8056 100%); color:white; padding:34px; border-radius:22px; margin-bottom:24px; }
        .padi-hero h1,.padi-hero h2,.padi-hero p { color:white; margin-top:0; }
        .padi-eyebrow { font-size:.78rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; opacity:.8; }
        .padi-result { background:#fff; border:1px solid #dce7df; border-left:6px solid var(--padi-green); border-radius:16px; padding:24px; margin:18px 0; }
        .padi-result .value { font-size:2.35rem; line-height:1.1; font-weight:750; color:var(--padi-green); }
        .padi-muted { color:#647168; }
        .padi-badge { display:inline-block; background:#e8f3ec; color:#1f6b45; border-radius:999px; padding:5px 10px; font-size:.82rem; font-weight:650; }
        [data-testid="stSidebar"] { background:#f0f5f1; border-right:1px solid #dde7df; }
        [data-testid="stSidebarNav"] a { border-radius:10px; }
        footer { visibility:hidden; }
        @media(max-width:700px){.block-container{padding:1.2rem}.padi-hero{padding:24px}.padi-result .value{font-size:1.8rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str, eyebrow: str | None = None) -> None:
    eyebrow_html = f'<div class="padi-eyebrow">{eyebrow}</div>' if eyebrow else ""
    st.markdown(
        f'<section class="padi-hero">{eyebrow_html}<h1>{title}</h1><p>{description}</p></section>',
        unsafe_allow_html=True,
    )


def format_period(value) -> str:
    period = pd.Period(value, freq="M")
    return f"{MONTHS_ID[period.month]} {period.year}"


def format_ton(value: float, decimals: int = 0) -> str:
    formatted = f"{float(value):,.{decimals}f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".") + " ton"


def format_number(value: float, decimals: int = 3) -> str:
    return f"{float(value):.{decimals}f}".replace(".", ",")
