import pandas as pd
import numpy as np
import os
import sys
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.model_selection import StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier, StackingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, balanced_accuracy_score, confusion_matrix
)
from imblearn.ensemble import BalancedRandomForestClassifier
from imblearn.pipeline import Pipeline as ImblearnPipeline
from xgboost import XGBClassifier
import lightgbm as lgb
from catboost import CatBoostClassifier

from src import config
from src.train import CLINICAL_FEATURES

df = pd.read_csv(config.PATH_PROCESSED_FEATURES)
X = df[CLINICAL_FEATURES]
y = df["hospital_expire_flag"]

preprocessor = ColumnTransformer(
    transformers=[('num', StandardScaler(), CLINICAL_FEATURES)],
    remainder='drop'
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

base_models = {
    "Logistic Regression": ("logistic_regression", ImblearnPipeline([('preproc', preprocessor), ('classifier', LogisticRegression(C=0.1, penalty='l2', solver='liblinear', class_weight='balanced', random_state=42))])),
    "CatBoost": ("catboost", ImblearnPipeline([('preproc', preprocessor), ('classifier', CatBoostClassifier(n_estimators=50, depth=2, learning_rate=0.05, auto_class_weights='Balanced', verbose=0, random_state=42))])),
    "LightGBM": ("lightgbm", ImblearnPipeline([('preproc', preprocessor), ('classifier', lgb.LGBMClassifier(n_estimators=50, max_depth=2, learning_rate=0.05, class_weight='balanced', verbose=-1, random_state=42))])),
    "ExtraTrees": ("extra_trees", ImblearnPipeline([('preproc', preprocessor), ('classifier', ExtraTreesClassifier(n_estimators=100, max_depth=3, min_samples_leaf=4, class_weight='balanced', random_state=42))])),
    "Random Forest": ("random_forest", ImblearnPipeline([('preproc', preprocessor), ('classifier', RandomForestClassifier(n_estimators=100, max_depth=3, min_samples_leaf=4, class_weight='balanced', random_state=42))])),
    "Balanced Random Forest": ("balanced_random_forest", ImblearnPipeline([('preproc', preprocessor), ('classifier', BalancedRandomForestClassifier(n_estimators=100, max_depth=3, min_samples_leaf=4, sampling_strategy='auto', random_state=42))])),
    "XGBoost": ("xgboost", ImblearnPipeline([('preproc', preprocessor), ('classifier', XGBClassifier(n_estimators=50, max_depth=2, learning_rate=0.05, scale_pos_weight=(len(y)-y.sum())/y.sum(), eval_metric='logloss', random_state=42))]))
}

pipeline_voting = VotingClassifier(estimators=[(k, v) for k, v in base_models.values()], voting='soft')
pipeline_stacking = StackingClassifier(estimators=[(k, v) for k, v in base_models.values()], final_estimator=LogisticRegression(C=1.0, random_state=42), cv=5, n_jobs=-1)

all_models = {
    **base_models,
    "Voting Ensemble": ("voting_ensemble", pipeline_voting),
    "Stacking Ensemble": ("stacking_ensemble", pipeline_stacking)
}

print("======================================================================")
print("       OUT-OF-FOLD (OOF) 5-FOLD CROSS VALIDATION AUDIT (N=140 STAYS)   ")
print("======================================================================")

results = []

for name, (model_id, pipeline) in all_models.items():
    oof_probs = np.zeros(len(y))
    
    for train_idx, val_idx in cv.split(X, y):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        pipeline.fit(X_tr, y_tr)
        oof_probs[val_idx] = pipeline.predict_proba(X_val)[:, 1]
        
    # Sweep Youden J optimal cutoff on full OOF predictions
    best_bal, best_t = -1, 0.5
    for t in np.linspace(0.1, 0.9, 81):
        bal = balanced_accuracy_score(y, (oof_probs >= t).astype(int))
        if bal > best_bal:
            best_bal = bal
            best_t = t
            
    y_pred = (oof_probs >= best_t).astype(int)
    acc = accuracy_score(y, y_pred)
    tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()
    spec = tn / (tn + fp)
    rec = recall_score(y, y_pred, zero_division=0)
    prec = precision_score(y, y_pred, zero_division=0)
    f1 = f1_score(y, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y, oof_probs)
    pr_auc = average_precision_score(y, oof_probs)
    comp_score = roc_auc + pr_auc + rec
    
    results.append({
        "Model Name": name,
        "Opt. Threshold": round(best_t, 2),
        "ROC-AUC": round(roc_auc, 4),
        "PR-AUC": round(pr_auc, 4),
        "Recall (Sens)": round(rec, 4),
        "Specificity": round(spec, 4),
        "Accuracy": round(acc, 4),
        "F1-Score": round(f1, 4),
        "Composite Score": round(comp_score, 4)
    })

df_res = pd.DataFrame(results).sort_values(by="Composite Score", ascending=False)
print(df_res.to_string(index=False))
print("======================================================================")
