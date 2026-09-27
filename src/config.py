from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ARTIFACT_DIR = PROJECT_ROOT / "artifacts"
REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
SPATIAL_DIR = PROJECT_ROOT / "data" / "spatial"

X_TRAIN_PATH = ARTIFACT_DIR / "X_train.csv"
Y_TRAIN_PATH = ARTIFACT_DIR / "y_train_asli.csv"
BEST_PARAMS_PATH = ARTIFACT_DIR / "tabpfn_best_params.joblib"
MODEL_CONFIG_PATH = ARTIFACT_DIR / "model_config.json"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"
VALIDATION_REFERENCE_PATH = ARTIFACT_DIR / "validation_reference.json"

HISTORICAL_INDEX_PATH = REFERENCE_DIR / "historis_index.csv"
MODEL_FULL_PATH = REFERENCE_DIR / "df_model_full.csv"