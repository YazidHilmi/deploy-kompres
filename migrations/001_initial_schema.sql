CREATE TABLE IF NOT EXISTS monthly_indices (
    id BIGSERIAL PRIMARY KEY,
    kabupaten TEXT NOT NULL,
    period DATE NOT NULL,
    ndvi_mean DOUBLE PRECISION NOT NULL,
    evi_mean DOUBLE PRECISION NOT NULL,
    savi_mean DOUBLE PRECISION NOT NULL,
    image_count INTEGER,
    source TEXT NOT NULL,
    quality_status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (kabupaten, period)
);

CREATE TABLE IF NOT EXISTS prediction_results (
    id UUID PRIMARY KEY,
    kabupaten TEXT NOT NULL,
    target_period DATE NOT NULL,
    estimated_production_ton DOUBLE PRECISION NOT NULL,
    model_version TEXT NOT NULL,
    index_source TEXT NOT NULL,
    input_features_json JSONB NOT NULL,
    quality_status TEXT NOT NULL,
    processing_seconds DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prediction_results_region_period
    ON prediction_results (kabupaten, target_period DESC);
