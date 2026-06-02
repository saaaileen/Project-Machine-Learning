import os
from typing import Optional, List

current_dir = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.normpath(os.path.join(current_dir, "../../../dataset/"))
MODEL_DIR = os.path.normpath(os.path.join(current_dir, "../../../model/"))

encoder = "label_encoder.joblib"
ENCODER_PATH = os.path.join(MODEL_DIR, encoder)

# The currently active dataset filename (mutable at runtime).
_active_dataset: str = "flows.csv"


def get_active_dataset() -> str:
    """Return the filename of the currently active dataset."""
    return _active_dataset


def set_active_dataset(filename: str) -> None:
    """Switch the active dataset to *filename* (must exist in DATASET_DIR)."""
    global _active_dataset
    path = os.path.join(DATASET_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {filename}")
    _active_dataset = filename


def list_datasets() -> List[str]:
    """Return all CSV/parquet files in the dataset directory."""
    if not os.path.isdir(DATASET_DIR):
        return []
    return sorted(
        f for f in os.listdir(DATASET_DIR)
        if f.endswith(".csv") or f.endswith(".parquet")
    )


def get_dataset_dir() -> str:
    return DATASET_DIR


def get_dataset_path() -> Optional[str]:
    path = os.path.join(DATASET_DIR, _active_dataset)
    if os.path.exists(path):
        return path
    return None


def get_encoder_path() -> Optional[str]:
    if os.path.exists(ENCODER_PATH):
        return ENCODER_PATH
    return None

# Keep DATASET_PATH for any legacy imports (resolves to the default dataset).
DATASET_PATH = os.path.join(DATASET_DIR, _active_dataset)