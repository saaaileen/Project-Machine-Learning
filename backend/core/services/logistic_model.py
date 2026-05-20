import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
)
import joblib

from preprocessing import DATASET_PATH

class LogisticModel:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = LabelEncoder()
        self.preprocess_data_info = None

    def load_data(self, dataset_path=DATASET_PATH):
        if "parquet" in dataset_path:
            df = pd.read_parquet(dataset_path)
        else:
            df = pd.read_csv(dataset_path)

        return df
    
    def load_data_info(self, info_path):
        if os.path.exists(info_path):
            self.preprocess_data_info = joblib.load(info_path)
        else:
            print(f"Preprocessing info file {info_path} not found. Please ensure it exists.")
    
    def load_model(self, model_path):
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            print(f"Model file {model_path} not found. Please train the model first.")

    def preprocess_data(self, df):
        if "activity" in df.columns:
            df = df.drop(columns=["activity"])

        # Separate features and target variable
        X = df

        if self.preprocess_data_info:
            zero_var_cols = self.preprocess_data_info["zero_var_cols"]
            high_corr_cols = self.preprocess_data_info["high_corr_cols"]
            feature_columns = self.preprocess_data_info["feature_columns"]
        else:
            print("Preprocessing info not found. Please load preprocessing info first.")
            return None, None
        
        cols_to_drop = list(set(zero_var_cols + high_corr_cols))
        X = df.drop(columns=cols_to_drop, errors="ignore")
        X = X.reindex(columns=feature_columns, fill_value=np.nan)

        return X, None

    def test_model(self, dataset_path=DATASET_PATH):
        df = self.load_data(dataset_path)
        X_test, y_test = self.preprocess_data(df)

        y_pred = self.model.predict(X_test)
        print(f"Predicted labels: {y_pred}")



        