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

        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)
        
        pca = PCA(n_components=3, random_state=42, svd_solver='full')
        X_pca = pca.fit_transform(X_scaled)

        return X_pca, y

    def test_model(self, dataset_path=DATASET_PATH):
        df = self.load_data(dataset_path)
        X_test, y_test = self.preprocess_data(df)

        y_pred = self.model.predict(X_test)
        print("KNN Model Classification Report:")
        print(f"Predicted labels: {y_pred}")
        print(f"Actual labels: {y_test}")
        print(classification_report(y_test, y_pred))
