import os

current_dir = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.normpath(os.path.join(current_dir, "../../../dataset/bccc-cpacket-cloud-ddos-2024-merged.parquet"))
