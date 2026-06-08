import pickle
import joblib
import warnings
warnings.filterwarnings('ignore')

model_configs = [
    ("LogReg", "logistic_regression_model.pkl", "logreg_preprocess_info.pkl"),
    ("LogReg2", "logisticRegression_model.pkl", "logisticRegression_preprocess_info.pkl"),
    ("KNN", "knn_model.pkl", "knn_preprocess_info.pkl"),
    ("Random Forest", "random_forest_model.pkl", "random_forest_preprocess_info.pkl"),
    ("SVM", "svm_model.pkl", "svm_preprocess_info.pkl"),
    ("XGBoost", "xgboost_model.pkl", "xgboost_preprocess_info.pkl"),
]

for name, mp, pp in model_configs:
    try:
        with open(mp, 'rb') as f:
            m = pickle.load(f)
        with open(pp, 'rb') as f:
            p = pickle.load(f)
        print(f"SUCCESS: {name}")
    except Exception as e:
        print(f"FAILED: {name} - {e}")

