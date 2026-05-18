import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib

from preprocessing import DATASET_PATH

class RandomForestModel:
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()

    def load_data(self):
        df = pd.read_parquet(DATASET_PATH)
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

        # Separate features and target variable
        X = df.drop(columns=["label"])
        y = df["label"]

        return X, y

    def test_model(self):
        df = self.load_data()
        X_test, y_test = self.preprocess_data(df)

        y_pred = self.model.predict(X_test)
        print("Random Forest Model Classification Report:")
        print(classification_report(y_test, y_pred))
