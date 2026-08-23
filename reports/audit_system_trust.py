import os
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)
from sklearn.model_selection import train_test_split

BASE_DIR = r"d:\ICU_Risk_Prediction_AI"
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "processed_clinical_features.csv")
MODEL_PATH = os.path.join(BASE_DIR, "data", "models", "best_model.joblib")

print("======================================================================")
print("             AUDITING SYSTEM TRUST & EMPIRICAL ACCURACY               ")
print("======================================================================")

# 1. Load Data
df = pd.read_csv(DATA_PATH)
X = df.drop(columns=["hospital_expire_flag", "stay_id", "subject_id", "hadm_id", "intime", "outtime"], errors="ignore")
y = df["hospital_expire_flag"]

# Stratified 80-20 split (matching train.py seed 42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

print(f"Total Cohort Stays:  {len(df)}")
print(f"Train Set Stays:     {len(X_train)} (Class 0: {(y_train==0).sum()}, Class 1: {(y_train==1).sum()})")
print(f"Test Set Stays:      {len(X_test)}  (Class 0: {(y_test==0).sum()}, Class 1: {(y_test==1).sum()})")
print("----------------------------------------------------------------------")

# 2. Load Serialized Champion Pipeline
pipe_dict = joblib.load(MODEL_PATH)
print("Keys in joblib dictionary:", list(pipe_dict.keys()))
model = pipe_dict["pipeline"]
threshold = pipe_dict["optimal_threshold"]
selected_features = pipe_dict["feature_names"]

print(f"Loaded Champion Pipeline: {model.named_steps['classifier'].__class__.__name__}")
print(f"Optimal Youden Threshold: {threshold}")
print(f"Selected Clinical Biomarkers ({len(selected_features)}): {selected_features}")
print("----------------------------------------------------------------------")

# 3. Compute Holdout Predictions & Probabilities
X_test_sub = X_test[selected_features]
y_prob = model.predict_proba(X_test_sub)[:, 1]
y_pred = (y_prob >= threshold).astype(int)

# 4. Calculate Exact Metrics
acc = accuracy_score(y_test, y_pred)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
spec = tn / (tn + fp) if (tn + fp) > 0 else 0
rec = recall_score(y_test, y_pred, zero_division=0)
prec = precision_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)

try:
    roc_auc = roc_auc_score(y_test, y_prob)
except Exception:
    roc_auc = 0.5

try:
    pr_auc = average_precision_score(y_test, y_prob)
except Exception:
    pr_auc = 0.0

comp_score = rec + roc_auc + pr_auc

print("EMPIRICAL HOLDOUT EVALUATION RESULTS (EXACT LIVE COMPUTATION):")
print(f"  - Accuracy:                  {acc:.4f} ({acc*100:.2f}%)")
print(f"  - Specificity (True Neg):    {spec:.4f} ({spec*100:.2f}%)  [{tn}/{tn+fp}]")
print(f"  - Recall / Sensitivity:     {rec:.4f} ({rec*100:.2f}%)   [{tp}/{tp+fn}]")
print(f"  - Precision:                 {prec:.4f}")
print(f"  - F1-Score:                  {f1:.4f}")
print(f"  - ROC-AUC Score:             {roc_auc:.4f}")
print(f"  - PR-AUC Score:              {pr_auc:.4f}")
print(f"  - Clinical Composite Score:  {comp_score:.4f} (Recall {rec:.4f} + ROC {roc_auc:.4f} + PR {pr_auc:.4f})")
print("======================================================================")
