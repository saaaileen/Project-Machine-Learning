# DDoS Attack Detection System

A machine learning project that classifies network traffic flows into three categories — **Benign**, **Attack**, and **Suspicious** — using the BCCC-cPacket Cloud DDoS 2024 dataset. The project covers the full pipeline: EDA, preprocessing, model training, evaluation, and a React-based web dashboard for visualizing detection results.

---

## Table of Contents

- [Project Description](#project-description)
- [Dataset & EDA](#dataset--eda)
- [Preprocessing Pipeline](#preprocessing-pipeline)
- [Model Results](#model-results)
- [Tech Stack](#tech-stack)
- [Links](#links)

---

## Project Description

Network-level DDoS attacks remain one of the most common and disruptive threats to online services. This project builds a multi-class traffic classifier that distinguishes normal traffic from attack traffic and flags borderline ("Suspicious") flows that may warrant further investigation.

**Three-class problem:**
| Class | Meaning |
|-------|---------|
| `Benign` | Normal, legitimate network traffic |
| `Attack` | Confirmed DDoS attack traffic |
| `Suspicious` | Anomalous traffic that does not clearly fit either category |

The system consists of:
- A **machine learning backend** — five models trained and compared on 540K+ network flow records
- A **React frontend dashboard** — real-time attack visualization, timeline analysis, severity classification, and mitigation recommendations
- A **REST API layer** (Express.js sample) for connecting the frontend to a live detection backend

---

## Dataset & EDA

**Dataset**: [BCCC-cPacket Cloud DDoS 2024](https://www.unb.ca/cic/datasets/ddos-2024.html)  
**File**: `bccc-cpacket-cloud-ddos-2024-merged.parquet`

### Raw Dataset Overview

| Property | Value |
|----------|-------|
| Total rows | 540,494 |
| Total columns | 318 (317 numeric + 1 label) |
| Missing values | 0 |
| Duplicate rows | 21,391 |
| Label classes | 3 |

All features are numeric (port numbers, packet counts, payload sizes, inter-arrival times, flow statistics, etc.). There are no categorical features beyond the target label.

### Class Distribution

| Class | Count | Percentage |
|-------|-------|-----------|
| Benign | 349,178 | 64.60% |
| Attack | 170,436 | 31.53% |
| Suspicious | 20,880 | 3.86% |

The dataset is **moderately imbalanced** — Benign traffic dominates, and Suspicious flows represent less than 4% of all records. This imbalance directly affects model behavior and was explicitly handled during training (class weights, balanced subsampling).

### Key EDA Findings

- **No missing data**: All 317 numeric columns are fully populated — no imputation was required at the feature level (though pipelines include a median imputer as a safety measure).
- **High feature redundancy**: A correlation analysis revealed extreme collinearity across many features. The top-20 highest-variance features already showed dense correlation clusters, motivating the aggressive correlation-based feature pruning in preprocessing.
- **Class separability**: A 2D PCA projection of a 15K-sample subset showed moderate-to-good visual separation between Benign and Attack, while Suspicious overlapped significantly with both — explaining why all models struggle most on that class.
- **Top discriminative features** (by ANOVA F-score): Flow duration, packet count statistics, inter-arrival timing features, and payload size distributions consistently ranked highest for class separation.
- **Feature distributions**: Most features are heavily right-skewed with long tails and outliers (especially for attack flows), making scaling essential for distance- and gradient-based models.

---

## Preprocessing Pipeline

`model/preprocess_pipeline.ipynb` — applied once, outputs shared by all five models.

### Steps

1. **Drop `activity` column** — not a network feature; removed before any split.

2. **Label encoding**
   ```
   Attack     → 0
   Benign     → 1
   Suspicious → 2
   ```

3. **Stratified train/val/test split** — preserves class proportions across all three sets.
   | Split | Rows | Ratio |
   |-------|------|-------|
   | Train | 432,395 | 80% |
   | Validation | 54,049 | 10% |
   | Test | 54,050 | 10% |

4. **Zero-variance column removal** — 3 columns with a single unique value across all training rows were dropped (no signal).

5. **High-correlation column removal** — features with pairwise Pearson correlation > 0.95 (computed on a 50K training sample) were pruned. This removed **152 columns**, reducing the feature space from 317 → **162 final features**.

All artifacts (`label_encoder.joblib`, `preprocessing_info.joblib`, and the six split `.parquet` files) are saved to `dataset/processed/` and loaded by each model notebook.

---

## Model Results

Five models were trained using `RandomizedSearchCV` (3-iter, 3-fold CV, `f1_macro` scoring) with explicit class imbalance handling. Evaluation is on the held-out test set (54,050 samples).

**Primary metric**: Macro F1 — weights all three classes equally, penalizing poor performance on the rare `Suspicious` class.  
**Secondary metric**: Weighted F1 — reflects overall system health weighted by class support.

### Summary Table

| Model | Accuracy | Precision (W) | Recall (W) | Macro F1 | Weighted F1 | ROC-AUC |
|-------|----------|---------------|------------|----------|-------------|---------|
| K-Nearest Neighbors | 0.8258 | 0.8278 | 0.8258 | 0.5949 | 0.8243 | 0.8892 |
| Logistic Regression | 0.7401 | 0.9365 | 0.7401 | 0.6295 | 0.8132 | — |
| SVM (SGD / Linear) | 0.8991 | 0.9047 | 0.8991 | 0.6953 | 0.8975 | 0.9453 |
| XGBoost | 0.9434 | 0.9667 | 0.9434 | 0.8449 | 0.9507 | 0.9976 |
| Random Forest | **0.9657** | **0.9683** | **0.9657** | **0.8835** | **0.9667** | **0.9983** |

*(W) = weighted average. ROC-AUC for SVM uses decision function scores; Logistic Regression ROC-AUC was not captured in the final notebook run.*

### Per-Class F1 Scores

| Model | Attack F1 | Benign F1 | Suspicious F1 |
|-------|-----------|-----------|---------------|
| KNN | 0.8000 | 0.8791 | 0.1056 |
| Logistic Regression | 0.8606 | 0.8266 | 0.2013 |
| SVM | 0.8757 | 0.9459 | 0.2643 |
| XGBoost | — | — | — *(macro 0.8449)* |
| Random Forest | — | — | — *(macro 0.8835)* |

### Analysis

**Random Forest** is the strongest overall performer — highest Macro F1 (0.8835), Weighted F1 (0.9667), and ROC-AUC (0.9983). With `max_depth=None` and 500 estimators, the ensemble captures complex decision boundaries well. `balanced_subsample` class weighting gave it the best `Suspicious` class handling among all models.

**XGBoost** is a close second — Macro F1 of 0.8449 with a near-perfect ROC-AUC (0.9976). Its advantage is GPU-accelerated training (`device='cuda'`), making it faster to iterate on larger parameter searches if needed.

**SVM (SGD-Linear)** achieves competitive Weighted F1 (0.8975) and is the fastest to train on this feature space, but its Macro F1 (0.6953) reveals it still struggles with `Suspicious` flows (F1 0.2643).

**Logistic Regression** is interpretable and fast but underperforms on `Suspicious` (F1 0.2013), indicating the class boundary for borderline flows is non-linear and cannot be captured with a linear model alone.

**KNN** with PCA (3 components, 98.8% variance retained) performs the worst on `Suspicious` (F1 0.1056). The aggressive dimensionality reduction to just 3 PCA components — while geometrically reasonable for 98.8% variance — collapses fine-grained distinctions that matter for the minority class.

**The `Suspicious` class is consistently the hardest across all models.** With only 3.86% representation and overlap with both Benign and Attack in feature space, this remains an open challenge. Future work could explore SMOTE oversampling, cost-sensitive loss functions, or a two-stage classifier (binary first, then Suspicious vs. rest).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML / Data | Python, scikit-learn, XGBoost, pandas, NumPy, joblib |
| Notebooks | Jupyter |
| Frontend | React 19, TypeScript 5.9, Vite 8, CSS3 |
| Backend (sample) | Node.js, Express.js |
| Dataset format | Parquet |

---

## Links
Live App   : https://huggingface.co/spaces/KenHoH/ML_Security <br>
Demo Video : https://drive.google.com/drive/folders/1iDnnv8V_erJpuA2zRys3Y8UTYXYzw1Ch?usp=sharing

