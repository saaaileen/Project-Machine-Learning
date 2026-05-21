import os
import pandas as pd
from typing import Any, Dict, List, Optional
from .logistic_model import LogisticModel
from .knn_model import KNNModel
from .random_forest_model import RandomForestModel
from .xgboost_model import XGBoostModel
from .preprocessing import get_dataset_path, get_encoder_path
from .svm_model import SVMModel
from pathlib import Path

# Columns surfaced to the user when browsing the dataset.
# These are high-level identifiers; all columns are still used by the model internally.
SUMMARY_COLUMNS: List[str] = [
    "duration",
    "packets_count",
    "bytes_rate",
    "packets_rate",
    "fwd_packets_rate",
    "bwd_packets_rate",
    "bwd_bytes_rate",
    "down_up_rate",
    "handshake_state",
    "syn_flag_counts",
    "ack_flag_counts",
    "psh_flag_counts",
    "rst_flag_counts",
    "fin_flag_counts",
    "total_payload_bytes",
    "fwd_total_payload_bytes",
    "bwd_total_payload_bytes",
    "label",
    "activity",
]

def get_list_of_models():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.normpath(os.path.join(current_dir, '../../../', 'model'))
    print(f"Model directory: {model_dir}")
    if not os.path.exists(model_dir): return []
    models = os.listdir(model_dir)
    models = [model for model in models if ".joblib" in model]
    models = [model for model in models if "preprocess_info" not in model]
    models = [model.split('.')[0] for model in models]
    models = [model.split('_')[0] for model in models]
    print(models)
    return list(set(models))


def get_dataset_rows(
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Return a paginated slice of the dataset with only the summary columns.

    Each row includes a ``row_index`` field (its 0-based position in the full
    dataset) so the client can reference specific rows when calling
    ``POST /api/models/use``.
    """
    dataset_path = get_dataset_path()
    if not dataset_path:
        raise FileNotFoundError("Dataset file not found, please generate it first")

    if "parquet" in dataset_path:
        df = pd.read_parquet(dataset_path)
    else:
        df = pd.read_csv(dataset_path)

    total_rows = len(df)

    # Keep only the summary columns that actually exist in this dataset
    existing_summary_cols = [c for c in SUMMARY_COLUMNS if c in df.columns]
    df_display = df[existing_summary_cols].copy()

    # Attach the absolute row index so the client can send it back unchanged
    df_display.insert(0, "row_index", range(total_rows))

    # Paginate
    df_page = df_display.iloc[offset : offset + limit]

    return {
        "total_rows": total_rows,
        "offset": offset,
        "limit": limit,
        "columns": ["row_index"] + existing_summary_cols,
        "rows": df_page.to_dict(orient="records"),
    }

def use_model(model_name: str = "logisticRegression", row_indices: Optional[List[int]] = None):

    BASE_DIR = os.path.join(Path(__file__).resolve().parent, "../../../model/")
    dataset_path = get_dataset_path()
    label_encoder_path = get_encoder_path() 

    if not dataset_path:
        raise FileNotFoundError(f"Dataset file not found, please generate it first")
    if not label_encoder_path:
        raise FileNotFoundError(f"Label encoder file not found, please generate it first")

    model = None
    if model_name == "logisticRegression":
        model = LogisticModel()
    elif model_name == "knn":
        model = KNNModel()
    elif model_name == "randomForest":
        model = RandomForestModel()
    elif model_name == "xgboost":
        model = XGBoostModel()
    elif model_name == "svm":
        model = SVMModel()
    else:
        raise ValueError(f"Model {model_name} not found. Please choose from {get_list_of_models()}")

    model_path = os.path.join(BASE_DIR, f'{model_name}_model.joblib')
    datainfo_path = os.path.join(BASE_DIR, f'{model_name}_preprocess_info.joblib')

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    if os.path.exists(datainfo_path):
        model.load_data_info(datainfo_path)

    model.load_model(model_path)
    return model.test_model(dataset_path, label_encoder_path, row_indices=row_indices)