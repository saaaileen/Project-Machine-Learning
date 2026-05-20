import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, RobustScaler
from sklearn.decomposition import PCA
from sklearn.metrics import classification_report
import joblib

from .preprocessing import DATASET_PATH

class KNNModel:
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.preprocess_data_info = None

    def load_data_info(self, info_path):
        if os.path.exists(info_path):
            self.preprocess_data_info = joblib.load(info_path)
        else:
            print(f"Preprocessing info file {info_path} not found. Please ensure it exists.")

    def load_data(self, dataset_path=DATASET_PATH):
        if "parquet" in dataset_path:
            df = pd.read_parquet(dataset_path)
        else:
            df = pd.read_csv(dataset_path)
        return df
    
    def load_model(self, model_path):
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            print(f"Model file {model_path} not found. Please train the model first.")

    def preprocess_data(self, df):
        if "activity" in df.columns:
            df = df.drop(columns=["activity"])

        df["label"] = self.label_encoder.fit_transform(df["label"])

        X = df.drop(columns=["label"])
        y = df["label"]

        if self.preprocess_data_info:
            zero_var_cols = self.preprocess_data_info["zero_var_cols"]
            high_corr_cols = self.preprocess_data_info["high_corr_cols"]
            feature_columns = self.preprocess_data_info["feature_columns"]
            scaler = self.preprocess_data_info["scaler"]
            pca = self.preprocess_data_info["pca"]
        else:
            print("Preprocessing info not found. Please load preprocessing info first.")
            return None, None
        
        cols_to_drop = list(set(zero_var_cols + high_corr_cols))
        X = df.drop(columns=cols_to_drop, errors="ignore")
        X = X.reindex(columns=feature_columns, fill_value=np.nan)

        X_scaled = scaler.transform(X)
        X_pca = pca.transform(X_scaled)

        return X_pca, y

    def test_model(self, dataset_path=DATASET_PATH):
        df = self.load_data(dataset_path)
        X_test, y_test = self.preprocess_data(df)

        y_pred = self.model.predict(X_test)
        print("KNN Model Classification Report:")
        print(f"Predicted labels: {y_pred}")
        print(f"Actual labels: {y_test}")
        print(classification_report(y_test, y_pred))
