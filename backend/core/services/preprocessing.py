import os

dataset = "flows.csv"
encoder = "label_encoder.joblib"

current_dir = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.normpath(os.path.join(current_dir, "../../../dataset/", dataset))
ENCODER_PATH = os.path.normpath(os.path.join(current_dir, "../../../model/", encoder))

def get_dataset_path():
    if os.path.exists(DATASET_PATH):
        return DATASET_PATH
    else: 
        return None
    
def get_encoder_path():
    if os.path.exists(ENCODER_PATH):
        return ENCODER_PATH
    else: 
        return None