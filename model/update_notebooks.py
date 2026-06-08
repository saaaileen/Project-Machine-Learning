import nbformat

def print_model_cells(notebook_path, keyword):
    try:
        nb = nbformat.read(notebook_path, as_version=4)
        for i, cell in enumerate(nb.cells):
            if cell.cell_type == 'code' and keyword in cell.source:
                print(f"--- {notebook_path} --- Cell {i}")
                print(cell.source[:300])
    except Exception as e:
        print(f"Error reading {notebook_path}: {e}")

print_model_cells('KNN.model.ipynb', 'KNeighborsClassifier')
print_model_cells('SVM.model.ipynb', 'LinearSVC')
print_model_cells('random_forest.ipynb', 'RandomForestClassifier')
print_model_cells('XGBoost.model.ipynb', 'XGBClassifier')
