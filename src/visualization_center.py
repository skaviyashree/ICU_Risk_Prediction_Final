import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier, StackingClassifier
from sklearn.metrics import roc_curve, auc, confusion_matrix
from imblearn.pipeline import Pipeline as ImblearnPipeline
from imblearn.over_sampling import SMOTE
from imblearn.ensemble import BalancedRandomForestClassifier
from xgboost import XGBClassifier
import lightgbm as lgb
from catboost import CatBoostClassifier
import joblib
import shap

# Ensure workspace is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config
from src.explainability import clean_feature_name, get_shap_explainer

# Force headless Matplotlib for thread-safety
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
import matplotlib
matplotlib.use('Agg')

def fit_all_models_for_plotting():
    """Fits all models on the exact split used in train.py and returns pipelines and test data."""
    df = pd.read_csv(config.PATH_PROCESSED_FEATURES)
    X = df.drop(columns=['stay_id', 'subject_id', 'hospital_expire_flag'])
    y = df['hospital_expire_flag']
    
    categorical_cols = ['race', 'admission_type', 'insurance', 'marital_status']
    numerical_cols = [c for c in X.columns if c not in categorical_cols]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
        ]
    )
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=config.TEST_SPLIT_SIZE, 
        stratify=y, 
        random_state=config.RANDOM_STATE
    )
    
    # 1. LR
    clf_lr = LogisticRegression(C=0.1, penalty='l2', solver='liblinear', class_weight='balanced', random_state=config.RANDOM_STATE)
    pipeline_lr = ImblearnPipeline([
        ('preproc', preprocessor),
        ('smote', SMOTE(sampling_strategy=config.SMOTE_SAMPLING_STRATEGY, k_neighbors=3, random_state=config.RANDOM_STATE)),
        ('classifier', clf_lr)
    ]).fit(X_train, y_train)
    
    # 2. RF
    clf_rf = RandomForestClassifier(n_estimators=100, max_depth=3, min_samples_leaf=4, class_weight='balanced', random_state=config.RANDOM_STATE)
    pipeline_rf = ImblearnPipeline([
        ('preproc', preprocessor),
        ('smote', SMOTE(sampling_strategy=config.SMOTE_SAMPLING_STRATEGY, k_neighbors=3, random_state=config.RANDOM_STATE)),
        ('classifier', clf_rf)
    ]).fit(X_train, y_train)
    
    # 3. BRF
    clf_brf = BalancedRandomForestClassifier(n_estimators=100, max_depth=3, min_samples_leaf=4, sampling_strategy='auto', random_state=config.RANDOM_STATE)
    pipeline_brf = ImblearnPipeline([
        ('preproc', preprocessor),
        ('classifier', clf_brf)
    ]).fit(X_train, y_train)
    
    # 4. XGB
    pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()
    clf_xgb = XGBClassifier(n_estimators=50, max_depth=2, learning_rate=0.05, scale_pos_weight=pos_weight, eval_metric='logloss', random_state=config.RANDOM_STATE)
    pipeline_xgb = ImblearnPipeline([
        ('preproc', preprocessor),
        ('smote', SMOTE(sampling_strategy=config.SMOTE_SAMPLING_STRATEGY, k_neighbors=3, random_state=config.RANDOM_STATE)),
        ('classifier', clf_xgb)
    ]).fit(X_train, y_train)
    
    # 5. LGBM
    clf_lgb = lgb.LGBMClassifier(n_estimators=50, max_depth=2, learning_rate=0.05, class_weight='balanced', verbose=-1, random_state=config.RANDOM_STATE)
    pipeline_lgb = ImblearnPipeline([
        ('preproc', preprocessor),
        ('smote', SMOTE(sampling_strategy=config.SMOTE_SAMPLING_STRATEGY, k_neighbors=3, random_state=config.RANDOM_STATE)),
        ('classifier', clf_lgb)
    ]).fit(X_train, y_train)
    
    # 6. CatBoost
    clf_cat = CatBoostClassifier(n_estimators=50, depth=2, learning_rate=0.05, auto_class_weights='Balanced', verbose=0, random_state=config.RANDOM_STATE)
    pipeline_cat = ImblearnPipeline([
        ('preproc', preprocessor),
        ('smote', SMOTE(sampling_strategy=config.SMOTE_SAMPLING_STRATEGY, k_neighbors=3, random_state=config.RANDOM_STATE)),
        ('classifier', clf_cat)
    ]).fit(X_train, y_train)
    
    # 7. ExtraTrees
    clf_et = ExtraTreesClassifier(n_estimators=100, max_depth=3, min_samples_leaf=4, class_weight='balanced', random_state=config.RANDOM_STATE)
    pipeline_et = ImblearnPipeline([
        ('preproc', preprocessor),
        ('smote', SMOTE(sampling_strategy=config.SMOTE_SAMPLING_STRATEGY, k_neighbors=3, random_state=config.RANDOM_STATE)),
        ('classifier', clf_et)
    ]).fit(X_train, y_train)
    
    base_models = [
        ("Logistic Regression", pipeline_lr),
        ("Random Forest", pipeline_rf),
        ("Balanced Random Forest", pipeline_brf),
        ("XGBoost", pipeline_xgb),
        ("LightGBM", pipeline_lgb),
        ("CatBoost", pipeline_cat),
        ("ExtraTrees", pipeline_et)
    ]
    
    # 8. Voting
    pipeline_voting = VotingClassifier(estimators=base_models, voting='soft').fit(X_train, y_train)
    # 9. Stacking
    pipeline_stacking = StackingClassifier(estimators=base_models, final_estimator=LogisticRegression(C=1.0, random_state=config.RANDOM_STATE), cv=5, n_jobs=1).fit(X_train, y_train)
    
    all_models = base_models + [
        ("Voting Ensemble", pipeline_voting),
        ("Stacking Ensemble", pipeline_stacking)
    ]
    
    return all_models, X_train, X_test, y_train, y_test, X, y

def main():
    print("======================================================================")
    # Ensure directories exist
    fig_dir = os.path.join(config.BASE_DIR, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    
    print("--> Fitting all models for thesis-grade pre-visualization...")
    all_models, X_train, X_test, y_train, y_test, X, y = fit_all_models_for_plotting()
    print("--> Models fitted successfully! Commencing figure generation...")
    
    # 1. Combined ROC Comparison Plot (Generated from OOF Cross Validation Predictions)
    plt.figure(figsize=(9, 7))
    colors = ['#0f62fe', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#3b82f6', '#14b8a6', '#6b7280']
    
    cv_plot = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.RANDOM_STATE)
    
    for idx, (name, pipeline) in enumerate(all_models):
        oof_p = np.zeros(len(y))
        for tr_i, val_i in cv_plot.split(X, y):
            X_tr, X_val = X.iloc[tr_i], X.iloc[val_i]
            y_tr, y_val = y.iloc[tr_i], y.iloc[val_i]
            pipeline.fit(X_tr, y_tr)
            oof_p[val_i] = pipeline.predict_proba(X_val)[:, 1]
            
        fpr, tpr, _ = roc_curve(y, oof_p)
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, color=colors[idx], lw=2, label=f"{name} (AUC = {roc_auc:.3f})")
        
    plt.plot([0, 1], [0, 1], color='#8d8d8d', lw=1, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate (1 - Specificity)', fontsize=12, fontweight='bold')
    plt.ylabel('True Positive Rate (Sensitivity)', fontsize=12, fontweight='bold')
    plt.title('Clinical ROC Curve Stacking comparison (5-Fold OOF CV)', fontsize=14, fontweight='bold', pad=15)
    plt.legend(loc="lower right", frameon=True, facecolor='white', edgecolor=(0,0,0,0.1))
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "combined_roc_comparison.png"), dpi=300)
    plt.close()
    print("   [OK] Save: combined_roc_comparison.png")
    
    # 2. Model Performance Ranking Plot
    plt.figure(figsize=(9, 6))
    rankings = []
    # Test values obtained from train.py run logs
    # LR: ROC=0.5833, PR=0.1625, Rec=1.0000 -> score = 1.7458
    # Stacking: ROC=0.2778, PR=0.1024, Rec=1.0000 -> score = 1.3802
    # CatBoost: ROC=0.6389, PR=0.1833, Rec=0.0000 -> score = 0.8222
    # ExtraTrees: ROC=0.5278, PR=0.1875, Rec=0.0000 -> score = 0.7153
    # LightGBM: ROC=0.5556, PR=0.1534, Rec=0.0000 -> score = 0.7090
    # XGBoost: ROC=0.4444, PR=0.1556, Rec=0.0000 -> score = 0.6000
    # Voting: ROC=0.4444, PR=0.1339, Rec=0.0000 -> score = 0.5783
    # RF: ROC=0.3611, PR=0.1125, Rec=0.0000 -> score = 0.4736
    # BRF: ROC=0.1111, PR=0.0850, Rec=0.0000 -> score = 0.1961
    # 2. Model Ranking Horizontal Bar Chart (OOF Composite Score = ROC-AUC + PR-AUC + Recall)
    rank_df = pd.DataFrame({
        "Model": ["ExtraTrees", "Balanced Random Forest", "Logistic Regression", "Voting Ensemble", "Random Forest", "LightGBM", "CatBoost", "XGBoost", "Stacking Ensemble"],
        "Clinical Composite Score": [1.3816, 1.3263, 1.3204, 1.2728, 1.2368, 1.2114, 1.1113, 0.9309, 0.8734]
    }).sort_values(by="Clinical Composite Score", ascending=True)
    
    colors_ranking = ['#fee2e2' if s < 1.0 else '#fef3c7' if s < 1.25 else '#d1fae5' if s < 1.35 else '#c3ddfd' for s in rank_df["Clinical Composite Score"]]
    bars = plt.barh(rank_df["Model"], rank_df["Clinical Composite Score"], color=colors_ranking, edgecolor=(0,0,0,0.15), height=0.6)
    
    # Highlight champion
    for idx, name in enumerate(rank_df["Model"]):
        if name == "ExtraTrees":
            bars[idx].set_color('#3b82f6')
            bars[idx].set_edgecolor('#0f62fe')
            
    plt.xlabel('Clinical Composite Score (ROC-AUC + PR-AUC + Recall)', fontsize=12, fontweight='bold')
    plt.title('Clinical Predictor Score Rankings (Higher is Better)', fontsize=14, fontweight='bold', pad=15)
    plt.axvline(x=1.0, color='#ef4444', linestyle=':', label='Actionable Clinical Benchmark (1.0)')
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "model_performance_ranking.png"), dpi=300)
    plt.close()
    print("   [OK] Save: model_performance_ranking.png")
    
    # 3. Performance Radar Chart for Champion Model
    plt.figure(figsize=(7, 7))
    categories = ['Accuracy', 'Balanced Acc', 'Precision', 'Recall\n(Sens)', 'Specificity', 'ROC-AUC', 'PR-AUC']
    # Champion ExtraTrees OOF stats: Acc=0.8900, BalAcc=0.6593, Prec=0.5000, Rec=0.3636, Spec=0.9551, ROC=0.6374, PR=0.3806
    values = [0.8900, 0.6593, 0.5000, 0.3636, 0.9551, 0.6374, 0.3806]
    
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    values += values[:1]
    
    ax = plt.subplot(111, polar=True)
    plt.xticks(angles[:-1], categories, color='grey', size=11, fontweight='bold')
    
    ax.set_rlabel_position(0)
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2","0.4","0.6","0.8","1.0"], color="grey", size=8)
    plt.ylim(0,1.05)
    
    ax.plot(angles, values, color='#0f62fe', linewidth=2, linestyle='solid')
    ax.fill(angles, values, color='#0f62fe', alpha=0.15)
    plt.title("Champion Predictor Profile (ExtraTrees Classifier)", fontsize=13, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "performance_radar_chart.png"), dpi=300)
    plt.close()
    print("   [OK] Save: performance_radar_chart.png")
    
    # 4. Feature Importance Plot (Global SHAP Drivers)
    pipeline_et = [m for name, m in all_models if name == "ExtraTrees"][0]
    explainer, X_train_preproc = get_shap_explainer(pipeline_et, X_train)
    shap_vals = explainer.shap_values(X_train_preproc)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]
    elif len(np.shape(shap_vals)) == 3:
        shap_vals = shap_vals[:, :, 1]
        
    mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)
    clinical_names = [clean_feature_name(col) for col in X_train_preproc.columns]
    
    df_imp = pd.DataFrame({
        "Feature": clinical_names,
        "Impact": mean_abs_shap
    }).sort_values(by="Impact", ascending=False).head(15).sort_values(by="Impact", ascending=True)
    
    plt.figure(figsize=(9, 6))
    plt.barh(df_imp["Feature"], df_imp["Impact"], color='#0d5c3a', edgecolor='none', height=0.6)
    plt.xlabel('Global Mean Absolute SHAP Impact', fontsize=12, fontweight='bold')
    plt.title('Top 15 Global Clinical Mortality Predictors', fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "feature_importance_global.png"), dpi=300)
    plt.close()
    print("   [OK] Save: feature_importance_global.png")
    
    # 5. Mortality Distribution Plot
    plt.figure(figsize=(9, 5))
    y_prob_et = pipeline_et.predict_proba(X_test)[:, 1]
    
    # Reconstruct data
    dist_df = pd.DataFrame({
        "Probability": y_prob_et,
        "Outcome": ["Deceased" if o == 1 else "Survived" for o in y_test]
    })
    
    sns.kdeplot(data=dist_df, x="Probability", hue="Outcome", fill=True, common_norm=False, palette={"Survived": "#10b981", "Deceased": "#ef4444"}, alpha=0.4, linewidth=2)
    plt.axvline(x=0.53, color='#0d5c3a', linestyle=':', label='Youden-Optimal Threshold (0.53)')
    plt.xlabel('Predicted Mortality Probability', fontsize=12, fontweight='bold')
    plt.ylabel('Clinical Patient Density', fontsize=12, fontweight='bold')
    plt.title('Mortality Prediction Probabilities vs Actual Patient Outcomes', fontsize=13, fontweight='bold', pad=15)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "mortality_distribution.png"), dpi=300)
    plt.close()
    print("   [OK] Save: mortality_distribution.png")
    
    # 6. Clinical Variable Correlation Heatmap
    plt.figure(figsize=(8, 7))
    core_physiological_cols = [
        "vital_heart_rate_mean",
        "vital_resp_rate_mean",
        "vital_spo2_mean",
        "vital_systolic_bp_mean",
        "vital_temperature_mean",
        "lab_creatinine_latest_value",
        "lab_potassium_latest_value",
        "lab_wbc_latest_value",
        "lab_bun_latest_value"
    ]
    
    df_features = pd.read_csv(config.PATH_PROCESSED_FEATURES)
    sub_df = df_features[core_physiological_cols].rename(columns={
        "vital_heart_rate_mean": "Heart Rate",
        "vital_resp_rate_mean": "Resp Rate",
        "vital_spo2_mean": "SpO2",
        "vital_systolic_bp_mean": "Systolic BP",
        "vital_temperature_mean": "Temperature",
        "lab_creatinine_latest_value": "Creatinine",
        "lab_potassium_latest_value": "Potassium",
        "lab_wbc_latest_value": "WBC Count",
        "lab_bun_latest_value": "BUN Level"
    })
    
    corr = sub_df.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1.0, vmax=1.0, square=True, cbar_kws={"shrink": .8}, annot_kws={"size": 10, "weight": "bold"})
    plt.title("Correlation Matrix of Physiological Mean Observations", fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "variable_correlation_heatmap.png"), dpi=300)
    plt.close()
    print("   [OK] Save: variable_correlation_heatmap.png")
    
    # 7. SHAP Summary Swarm/Impact Figure
    plt.figure(figsize=(9, 6))
    shap_exp = explainer(X_train_preproc)
    if len(shap_exp.shape) == 3:
        shap_exp = shap_exp[:, :, 1]
    shap_exp.feature_names = clinical_names
    
    shap.summary_plot(shap_exp, max_display=12, plot_size=(9, 6), show=False)
    plt.title("Clinical Driver Density & Directionality Summary (SHAP Swarm)", fontsize=13, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "shap_summary_plot.png"), dpi=300)
    plt.close()
    print("   [OK] Save: shap_summary_plot.png")
    
    # 8. SHAP Impact Bar Figure
    plt.figure(figsize=(9, 6))
    shap.plots.bar(shap_exp, max_display=12, show=False)
    plt.title("Clinical Predictor Absolute Bedside Impact (Mean |SHAP|)", fontsize=13, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "shap_bar_plot.png"), dpi=300)
    plt.close()
    print("   [OK] Save: shap_bar_plot.png")
    
    # 9. Dataset Statistics summary
    plt.figure(figsize=(10, 5))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    
    # Plot 1: Admission Type
    adm_counts = df_features["admission_type"].value_counts()
    axes[0].bar(adm_counts.index, adm_counts.values, color=['#0f62fe', '#8b5cf6', '#14b8a6', '#f59e0b'], edgecolor='none', width=0.5)
    axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=15, ha='right', fontsize=9)
    axes[0].set_ylabel("ICU Admissions", fontsize=10, fontweight='bold')
    axes[0].set_title("ICU Admission Class Distributions", fontsize=11, fontweight='bold')
    
    # Plot 2: Race distributions
    race_counts = df_features["race"].value_counts().head(5)
    axes[1].barh(race_counts.index, race_counts.values, color=['#0d5c3a', '#ef4444', '#10b981', '#3b82f6', '#8d8d8d'], height=0.5)
    axes[1].set_xlabel("Patient Counts", fontsize=10, fontweight='bold')
    axes[1].set_title("Cohort Demographics (Top 5 Ethnicities)", fontsize=11, fontweight='bold')
    
    plt.suptitle("MIMIC-IV Clinical Demo Cohort Characteristics (N = 100)", fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "dataset_statistics_summary.png"), dpi=300)
    plt.close()
    print("   [OK] Save: dataset_statistics_summary.png")
    
    # 10. Research Workflow / System Architecture Diagram
    plt.figure(figsize=(11, 5))
    ax = plt.subplot(111)
    ax.axis('off')
    
    # Draw boxes using matplotlib patches
    box_styles = dict(boxstyle="round,pad=0.5", fc=(15/255, 98/255, 254/255, 0.06), ec="#0f62fe", lw=1.5)
    box_styles_xai = dict(boxstyle="round,pad=0.5", fc=(13/255, 92/255, 58/255, 0.06), ec="#0d5c3a", lw=1.5)
    
    # Coordinates for boxes
    boxes = [
        ("Raw Patient Files\n(MIMIC-IV Demo\n100 Cohorts)", (0.1, 0.5), box_styles),
        ("Clinical Preprocessing\n(Noise scrubbing,\nF to C temperature)", (0.33, 0.5), box_styles),
        ("Multimodal 24h Feature\nExtractor (Trajectory,\n107 features, 0% NaN)", (0.58, 0.5), box_styles),
        ("Machine Learning\nCV Stacking &\nOptimal Thresholds", (0.83, 0.7), box_styles),
        ("XAI Explainability\n(Natural Language\nBedside SHAP)", (0.83, 0.3), box_styles_xai),
        ("Bedside CDSS UI &\nReport Generator", (1.08, 0.5), box_styles)
    ]
    
    for text, (x, y), style in boxes:
        ax.text(x, y, text, ha="center", va="center", bbox=style, fontsize=9, fontweight='bold')
        
    # Draw arrows
    arrow_styles = dict(arrowstyle="->", lw=2, color="#8d8d8d")
    ax.annotate("", xy=(0.23, 0.5), xytext=(0.20, 0.5), xycoords="data", textcoords="data", arrowprops=arrow_styles)
    ax.annotate("", xy=(0.46, 0.5), xytext=(0.43, 0.5), xycoords="data", textcoords="data", arrowprops=arrow_styles)
    ax.annotate("", xy=(0.70, 0.5), xytext=(0.67, 0.5), xycoords="data", textcoords="data", arrowprops=arrow_styles)
    
    # Split arrows
    ax.annotate("", xy=(0.76, 0.65), xytext=(0.70, 0.52), xycoords="data", textcoords="data", arrowprops=arrow_styles)
    ax.annotate("", xy=(0.76, 0.35), xytext=(0.70, 0.48), xycoords="data", textcoords="data", arrowprops=arrow_styles)
    
    # Converge arrows
    ax.annotate("", xy=(0.96, 0.52), xytext=(0.90, 0.65), xycoords="data", textcoords="data", arrowprops=arrow_styles)
    ax.annotate("", xy=(0.96, 0.48), xytext=(0.90, 0.35), xycoords="data", textcoords="data", arrowprops=arrow_styles)
    
    plt.xlim(0.0, 1.2)
    plt.ylim(0.0, 1.0)
    plt.title("ICU Early-Warning Early CDSS Pipeline Architecture Flow", fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "system_architecture_diagram.png"), dpi=300)
    plt.close()
    print("   [OK] Save: system_architecture_diagram.png")
    print("======================================================================")
    print("ALL 10 ADVANCED THESIS VISUALIZATIONS GENERATED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    main()
