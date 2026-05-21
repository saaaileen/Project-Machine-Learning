import os
from typing import List, Optional
import pandas as pd
import joblib

class RandomForestModel:
    def __init__(self):
        self.model = None

    def load_data(self, dataset_path):
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

        X = df.drop(columns=["label"])
        return X

    def test_model(self, dataset_path, label_encoder_path, row_indices: Optional[List[int]] = None):
        df = self.load_data(dataset_path)

        if row_indices is not None:
            invalid = [i for i in row_indices if i < 0 or i >= len(df)]
            if invalid:
                raise IndexError(f"Row indices out of range: {invalid}. Dataset has {len(df)} rows.")
            df_selected = df.iloc[row_indices].reset_index(drop=True)
        else:
            df_selected = df.reset_index(drop=True)

        X_test = self.preprocess_data(df_selected)
        le = joblib.load(label_encoder_path)

        y_pred = self.model.predict(X_test)
        y_pred_labels = le.inverse_transform(y_pred)

        result_df = df_selected.copy()
        result_df["predicted_label"] = y_pred_labels
        return result_df.to_dict(orient="records")