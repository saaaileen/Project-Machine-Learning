import os 
from .logistic_model import LogisticModel
from .knn_model import KNNModel
from .random_forest_model import RandomForestModel
from .xgboost_model import XGBoostModel
from .preprocessing import get_dataset_path, get_encoder_path
from svm_model import SVMModel
from pathlib import Path

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

def use_model(model_name="logisticRegression"):

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
    return model.test_model(dataset_path, label_encoder_path)