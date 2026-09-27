"""Penyimpanan indeks bulanan dan hasil prediksi."""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import Date, DateTime, Float, Integer, String, Text, UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.config import PROJECT_ROOT


class Base(DeclarativeBase):
    pass


class MonthlyIndex(Base):
    __tablename__ = "monthly_indices"
    __table_args__ = (UniqueConstraint("kabupaten", "period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kabupaten: Mapped[str] = mapped_column(String(80), nullable=False)
    period: Mapped[date] = mapped_column(Date, nullable=False)
    ndvi_mean: Mapped[float] = mapped_column(Float, nullable=False)
    evi_mean: Mapped[float] = mapped_column(Float, nullable=False)
    savi_mean: Mapped[float] = mapped_column(Float, nullable=False)
    image_count: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    quality_status: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kabupaten: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    target_period: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    estimated_production_ton: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    index_source: Mapped[str] = mapped_column(String(120), nullable=False)
    input_features_json: Mapped[str] = mapped_column(Text, nullable=False)
    quality_status: Mapped[str] = mapped_column(String(40), nullable=False)
    processing_seconds: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def create_database_engine(database_url: str | None = None):
    if not database_url:
        local_path = Path(PROJECT_ROOT) / "data" / "padi_local.db"
        local_path.parent.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{local_path.as_posix()}"

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    options = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **options)


def initialize_database(engine) -> None:
    Base.metadata.create_all(engine)


def seed_monthly_indices(engine, history: pd.DataFrame) -> int:
    """Tambahkan indeks historis yang belum ada; aman dipanggil berulang kali."""
    prepared = history.copy()
    prepared["Period"] = prepared["Period"].map(_as_date)

    with Session(engine) as session:
        existing = set(session.execute(select(MonthlyIndex.kabupaten, MonthlyIndex.period)))
        rows = []
        for row in prepared.itertuples(index=False):
            if (row.Kabupaten, row.Period) in existing:
                continue
            rows.append(MonthlyIndex(
                kabupaten=row.Kabupaten, period=row.Period, ndvi_mean=float(row.NDVI_mean),
                evi_mean=float(row.EVI_mean), savi_mean=float(row.SAVI_mean), image_count=None,
                source="historis_index.csv", quality_status="valid",
            ))
        session.add_all(rows)
        session.commit()
        return len(rows)


def upsert_monthly_index(engine, *, kabupaten: str, period, ndvi_mean: float, evi_mean: float,
                         savi_mean: float, image_count: int | None, source: str,
                         quality_status: str = "valid") -> str:
    """Simpan hasil GEE baru atau perbarui kabupaten-bulan yang sudah ada."""
    period_date = _as_date(period)
    with Session(engine) as session:
        record = session.scalar(select(MonthlyIndex).where(
            MonthlyIndex.kabupaten == kabupaten, MonthlyIndex.period == period_date,
        ))
        action = "updated" if record else "inserted"
        if record is None:
            record = MonthlyIndex(kabupaten=kabupaten, period=period_date)
            session.add(record)
        record.ndvi_mean, record.evi_mean, record.savi_mean = float(ndvi_mean), float(evi_mean), float(savi_mean)
        record.image_count, record.source = image_count, source
        record.quality_status, record.created_at = quality_status, datetime.now(timezone.utc)
        session.commit()
    return action


def load_monthly_indices(engine) -> pd.DataFrame:
    with Session(engine) as session:
        records = session.scalars(select(MonthlyIndex).order_by(MonthlyIndex.kabupaten, MonthlyIndex.period)).all()
    return pd.DataFrame([{
        "Kabupaten": record.kabupaten, "Tahun": record.period.year, "Bulan": record.period.month,
        "tanggal": record.period.isoformat(), "NDVI_mean": record.ndvi_mean,
        "EVI_mean": record.evi_mean, "SAVI_mean": record.savi_mean,
        "image_count": record.image_count, "source": record.source,
        "quality_status": record.quality_status,
    } for record in records])


def database_counts(engine) -> dict:
    with Session(engine) as session:
        return {
            "monthly_indices": len(session.scalars(select(MonthlyIndex.id)).all()),
            "prediction_results": len(session.scalars(select(PredictionResult.id)).all()),
        }


def existing_index_periods(engine) -> set[tuple[str, pd.Period]]:
    with Session(engine) as session:
        rows = session.execute(select(MonthlyIndex.kabupaten, MonthlyIndex.period)).all()
    return {(kabupaten, pd.Period(period, freq="M")) for kabupaten, period in rows}


def save_prediction(engine, *, kabupaten: str, target_period, estimated_production_ton: float,
                    model_version: str, index_source: str, input_features: dict,
                    quality_status: str = "valid", processing_seconds: float | None = None) -> str:
    prediction_id = str(uuid.uuid4())
    values = {key: float(value) for key, value in input_features.items()}
    record = PredictionResult(
        id=prediction_id, kabupaten=kabupaten, target_period=_as_date(target_period),
        estimated_production_ton=float(estimated_production_ton), model_version=model_version,
        index_source=index_source, input_features_json=json.dumps(values), quality_status=quality_status,
        processing_seconds=float(processing_seconds) if processing_seconds is not None else None,
    )
    with Session(engine) as session:
        session.add(record)
        session.commit()
    return prediction_id


def list_predictions(engine, kabupaten: str | None = None) -> pd.DataFrame:
    statement = select(PredictionResult)
    if kabupaten:
        statement = statement.where(PredictionResult.kabupaten == kabupaten)
    statement = statement.order_by(PredictionResult.created_at.desc())
    with Session(engine) as session:
        records = session.scalars(statement).all()
    return pd.DataFrame([_prediction_to_dict(record) for record in records])


def get_prediction(engine, prediction_id: str) -> dict | None:
    with Session(engine) as session:
        record = session.get(PredictionResult, prediction_id)
        return _prediction_to_dict(record) if record else None


def _as_date(value) -> date:
    return value.to_timestamp().date() if isinstance(value, pd.Period) else pd.Timestamp(value).date()


def _prediction_to_dict(record: PredictionResult) -> dict:
    return {
        "id": record.id, "kabupaten": record.kabupaten, "target_period": record.target_period,
        "estimated_production_ton": record.estimated_production_ton,
        "model_version": record.model_version, "index_source": record.index_source,
        "input_features": json.loads(record.input_features_json), "quality_status": record.quality_status,
        "processing_seconds": record.processing_seconds, "created_at": record.created_at,
    }
