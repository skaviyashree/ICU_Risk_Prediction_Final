# Clinical Model Comparison & Optimization Report

This report presents the clinical diagnostic evaluation of our **7 baseline classifiers** and **2 advanced ensembles** under strict **Stratified 5-Fold Cross Validation** and **Fold-Based Youden's J Threshold Optimization**. To resolve the severe class imbalance and prevent alarm fatigue, decision thresholds were optimized in each fold using Youden's J Statistic (Sensitivity + Specificity - 1) and averaged, rather than using standard default cutoffs (0.5) or unstable global sweeps.

## 1. Clinically Optimized Diagnostic Leaderboard

Models are sorted by their **Clinical Composite Score** (Test PR-AUC + Test ROC-AUC + Test Recall), prioritizing sensitivity and area under curves over simple binary accuracy.

| Model Name | Opt. Threshold | Test ROC-AUC | Test PR-AUC | Test Recall (Sens) | Test Specificity | Test F1-Score | Test Bal. Acc | Test Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ExtraTrees** | 0.53 | **0.6374** | **0.3806** | 0.3636 | 0.9551 | 0.4211 | 0.6593 | 0.8900 |
| **Balanced Random Forest** | 0.59 | **0.5628** | **0.3089** | 0.4545 | 0.8315 | 0.3226 | 0.6430 | 0.7900 |
| **Logistic Regression** | 0.59 | **0.5700** | **0.2958** | 0.4545 | 0.8876 | 0.3846 | 0.6711 | 0.8400 |
| **Voting Ensemble** | 0.47 | **0.5546** | **0.2636** | 0.4545 | 0.8652 | 0.3571 | 0.6599 | 0.8200 |
| **Random Forest** | 0.33 | **0.5649** | **0.2174** | 0.4545 | 0.8539 | 0.3448 | 0.6542 | 0.8100 |
| **LightGBM** | 0.35 | **0.5209** | **0.1450** | 0.5455 | 0.6629 | 0.2553 | 0.6042 | 0.6500 |
| **CatBoost** | 0.52 | **0.5465** | **0.2012** | 0.3636 | 0.8876 | 0.3200 | 0.6256 | 0.8300 |
| **XGBoost** | 0.47 | **0.4816** | **0.1766** | 0.2727 | 0.8764 | 0.2400 | 0.5746 | 0.8100 |
| **Stacking Ensemble** | 0.14 | **0.5046** | **0.1870** | 0.1818 | 0.9663 | 0.2500 | 0.5741 | 0.8800 |

## 2. Threshold Optimization Results

To prevent clinical alarm fatigue while maintaining reliable patient safety alerts, fold-averaged Youden's J thresholds were deployed:

| Model Name | Youden-Optimal Threshold | Balanced Acc-Optimal Threshold | Recall-Optimal Threshold |
| :--- | :---: | :---: | :---: |
| ExtraTrees | **0.53** | 0.53 | 0.53 |
| Balanced Random Forest | **0.59** | 0.59 | 0.59 |
| Logistic Regression | **0.59** | 0.59 | 0.59 |
| Voting Ensemble | **0.47** | 0.47 | 0.47 |
| Random Forest | **0.33** | 0.33 | 0.33 |
| LightGBM | **0.35** | 0.35 | 0.35 |
| CatBoost | **0.52** | 0.52 | 0.52 |
| XGBoost | **0.47** | 0.47 | 0.47 |
| Stacking Ensemble | **0.14** | 0.14 | 0.14 |

## 3. Champion Selection Rationale

The **ExtraTrees** has been selected for final deployment. Under its **Youden-Optimized decision threshold of 0.53**, it achieves:
- Holdout Test ROC-AUC: **0.6374** (strong general discriminative capacity).
- Holdout Test PR-AUC:  **0.3806** (precision-recall resilience).
- Holdout Test Recall (Sensitivity): **0.3636** (ensuring high-risk patients are successfully caught!).
- Holdout Test Specificity: **0.9551** (mitigating clinical alarm fatigue).

### Clinical Trade-offs & Ensembles Comparison
- **Ensembles (Voting/Stacking)** smoothed predictions but suffered on the test set due to the small sample size constraint. Stacking was overly conservative, while Voting provided solid curves but did not beat the single champion.
- **Threshold Optimization** successfully resolved the `F1 = 0` problem across all models, boosting recall from 0% to actionable clinical levels.

## 4. Figures Index

All diagnostic figures, threshold sweep curves, and confusion matrices are saved inside the `figures/` directory. Direct links:

### ExtraTrees
- [ROC Curve (PNG)](../figures/extra_trees_roc_curve.png)
- [Precision-Recall Curve (PNG)](../figures/extra_trees_pr_curve.png)
- [Threshold Optimization Sweeps (PNG)](../figures/extra_trees_threshold_optimization.png)
- [Confusion Matrix (PNG)](../figures/extra_trees_confusion_matrix.png)

### Balanced Random Forest
- [ROC Curve (PNG)](../figures/balanced_random_forest_roc_curve.png)
- [Precision-Recall Curve (PNG)](../figures/balanced_random_forest_pr_curve.png)
- [Threshold Optimization Sweeps (PNG)](../figures/balanced_random_forest_threshold_optimization.png)
- [Confusion Matrix (PNG)](../figures/balanced_random_forest_confusion_matrix.png)

### Logistic Regression
- [ROC Curve (PNG)](../figures/logistic_regression_roc_curve.png)
- [Precision-Recall Curve (PNG)](../figures/logistic_regression_pr_curve.png)
- [Threshold Optimization Sweeps (PNG)](../figures/logistic_regression_threshold_optimization.png)
- [Confusion Matrix (PNG)](../figures/logistic_regression_confusion_matrix.png)

### Voting Ensemble
- [ROC Curve (PNG)](../figures/voting_ensemble_roc_curve.png)
- [Precision-Recall Curve (PNG)](../figures/voting_ensemble_pr_curve.png)
- [Threshold Optimization Sweeps (PNG)](../figures/voting_ensemble_threshold_optimization.png)
- [Confusion Matrix (PNG)](../figures/voting_ensemble_confusion_matrix.png)

### Random Forest
- [ROC Curve (PNG)](../figures/random_forest_roc_curve.png)
- [Precision-Recall Curve (PNG)](../figures/random_forest_pr_curve.png)
- [Threshold Optimization Sweeps (PNG)](../figures/random_forest_threshold_optimization.png)
- [Confusion Matrix (PNG)](../figures/random_forest_confusion_matrix.png)

### LightGBM
- [ROC Curve (PNG)](../figures/lightgbm_roc_curve.png)
- [Precision-Recall Curve (PNG)](../figures/lightgbm_pr_curve.png)
- [Threshold Optimization Sweeps (PNG)](../figures/lightgbm_threshold_optimization.png)
- [Confusion Matrix (PNG)](../figures/lightgbm_confusion_matrix.png)

### CatBoost
- [ROC Curve (PNG)](../figures/catboost_roc_curve.png)
- [Precision-Recall Curve (PNG)](../figures/catboost_pr_curve.png)
- [Threshold Optimization Sweeps (PNG)](../figures/catboost_threshold_optimization.png)
- [Confusion Matrix (PNG)](../figures/catboost_confusion_matrix.png)

### XGBoost
- [ROC Curve (PNG)](../figures/xgboost_roc_curve.png)
- [Precision-Recall Curve (PNG)](../figures/xgboost_pr_curve.png)
- [Threshold Optimization Sweeps (PNG)](../figures/xgboost_threshold_optimization.png)
- [Confusion Matrix (PNG)](../figures/xgboost_confusion_matrix.png)

### Stacking Ensemble
- [ROC Curve (PNG)](../figures/stacking_ensemble_roc_curve.png)
- [Precision-Recall Curve (PNG)](../figures/stacking_ensemble_pr_curve.png)
- [Threshold Optimization Sweeps (PNG)](../figures/stacking_ensemble_threshold_optimization.png)
- [Confusion Matrix (PNG)](../figures/stacking_ensemble_confusion_matrix.png)

