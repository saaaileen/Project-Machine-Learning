import os
import numpy as np
import pandas as pd

import joblib

class LogisticModel:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.preprocess_data_info = None

    def load_data(self, dataset_path):
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

        return X 

    def test_model(self, dataset_path, label_encoder_path):
        df = self.load_data(dataset_path)
        X_test = self.preprocess_data(df)
        le = joblib.load(label_encoder_path)
        

        y_pred = self.model.predict(X_test)
        y_pred = le.inverse_transform(y_pred)
        return y_pred


        