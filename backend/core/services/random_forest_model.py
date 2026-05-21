import os
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

    def test_model(self, dataset_path, label_encoder_path):
        df = self.load_data(dataset_path)
        X_test = self.preprocess_data(df)
        le = joblib.load(label_encoder_path)
        

        y_pred = self.model.predict(X_test)
        y_pred = le.inverse_transform(y_pred)
        return y_pred