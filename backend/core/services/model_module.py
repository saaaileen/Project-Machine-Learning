import os 

def get_list_of_models():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.normpath(os.path.join(current_dir, '../../../', 'model'))
    print(f"Model directory: {model_dir}")
    if not os.path.exists(model_dir): return []
    models = os.listdir(model_dir)
    models = [model for model in models if ".joblib" in model]
    models = [model.split('.')[0] for model in models]
    return list(set(models))

def use_model(model_name: str):
    