"""Akses konfigurasi, data, dan model bersama untuk halaman Streamlit."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src.artifacts import load_training_artifacts
from src.config import HISTORICAL_INDEX_PATH
from src.database import create_database_engine, initialize_database, load_monthly_indices, seed_monthly_indices
from src.features import prepare_index_history
from src.model import fit_model


def get_secret(name: str):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets[name]
    except (KeyError, FileNotFoundError):
        return None


@st.cache_data
def load_reference_history():
    return prepare_index_history(pd.read_csv(HISTORICAL_INDEX_PATH))


@st.cache_resource
def get_engine(database_url: str | None = None):
    engine = create_database_engine(database_url or get_secret("DATABASE_URL"))
    initialize_database(engine)
    seed_monthly_indices(engine, load_reference_history())
    return engine


def load_index_history():
    frame = load_monthly_indices(get_engine())
    return prepare_index_history(frame) if not frame.empty else load_reference_history()


@st.cache_resource
def get_tabpfn_model():
    artifacts = load_training_artifacts()
    model = fit_model(
        X_train=artifacts["X_train"], y_train=artifacts["y_train"],
        best_params=artifacts["best_params"], access_token=get_secret("TABPFN_TOKEN"),
    )
    return model, artifacts
