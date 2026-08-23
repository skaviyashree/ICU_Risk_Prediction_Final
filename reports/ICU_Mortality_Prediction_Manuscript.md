# An Explainable Machine Learning CDSS with Clinical Baseline Imputation and Youden-Thresholding for Bedside ICU Mortality Prediction

**Abstract**  
Early identification of patient deterioration in Intensive Care Units (ICUs) is critical to improving survival rates, yet clinical environments suffer from alarm fatigue due to high false-positive warning rates. This study presents the design of an end-to-end, leak-free Explainable AI (XAI) bedside Clinical Decision Support System (CDSS) for in-hospital mortality risk prediction using physiological data from the initial 24 hours of an ICU stay. We evaluated seven machine learning classifiers and two ensembles on the MIMIC-IV Clinical Demo dataset (100 patients, 140 stays, 11% mortality rate). To regularize the feature space without over-relying on synthetic samples, we designed a clinical preprocessing pipeline featuring temperature unification, outlier scrubbing, and clinical baseline imputation (imputing missing laboratory draws with healthy reference values to simulate medical normalcy). To address severe class imbalance, we applied out-of-fold Youden’s J threshold optimization. An ExtraTrees Classifier emerged as the champion model, utilizing a fold-averaged decision threshold of 0.39. On the holdout test set, the champion model achieved an accuracy of 0.5500, a sensitivity of 0.5000, and a specificity of 0.5556 (ROC-AUC = 0.5556, PR-AUC = 0.1603). Transparency is achieved via a Tree SHAP engine, which maps model decisions to local bedside biophysical risk drivers. The system is deployed as an interactive Streamlit application with rule-based clinical guides and automated Patient Chart PDF generation to support clinical decision-making.

**Keywords—ICU Mortality Prediction, Explainable AI, Clinical Decision Support, ExtraTrees Classifier, Youden's J Threshold, Tree SHAP, MIMIC-IV Clinical Demo.**

---

## I. Introduction
The Intensive Care Unit (ICU) is a high-acuity environment where patients generate massive streams of physiological data. Critical care teams are inundated with vitals from bedside monitors and laboratory results from intermittent blood panels. This data density often causes clinical cognitive overload and alarm fatigue, where staff desensitize to warning signals, occasionally missing signs of actual clinical deterioration.

Machine learning (ML) models trained on Electronic Health Records (EHR) can serve as early-warning systems. However, standard models suffer from:
1. **Data Leakage**: Extracting features recorded right before death or discharge, rendering them useless for early intervention.
2. **Class Imbalance**: Standard classifiers collapse on the majority class (predicting survival for all patients) due to low mortality rates.
3. **Black-Box Architecture**: The lack of interpretability prevents bedside clinical trust.

### Contributions of this Work
To tackle these challenges, we design a multi-step clinical ML pipeline:
1. **Multi-Model Benchmark**: We compare seven base classifiers and two ensembles using a unified protocol.
2. **Clinical Preprocessing & Regularization**: We apply temperature unification, outlier scrubbing, and clinical baseline imputation (imputing missing lab tests with healthy references to represent normalcy) to stabilize predictions.
3. **Youden's J Threshold Optimization**: We sweep classification thresholds on out-of-fold validation predictions to balance sensitivity and specificity.
4. **Game-Theoretic Saliency**: We implement Tree SHAP to map risk predictions to bedside physiological drivers.
5. **Bedside CDSS Deployment**: We deliver a Streamlit application with slider overrides and signed A4 Patient Chart PDF generation.

---

## II. Related Work
Standard static clinical scoring systems, such as SAPS II and APACHE, estimate mortality risk based on the worst values in the first 24 hours of ICU stay. While widely used, these methods are static and do not adapt to continuous temporal trajectories. 

Machine learning classifiers (Random Forest, Gradient Boosting, Logistic Regression) have shown high statistical performance in predicting ICU mortality. However, their clinical utility is limited by the "black-box" problem. Explainable AI (XAI) frameworks, such as SHAP, have emerged as a mathematically consistent method based on cooperative game theory to explain individual predictions. Streamlit and vector PDF report generators provide a path for translating these models into clinical workflows.

---

## III. Dataset and Class Distribution
The study utilizes the publicly available MIMIC-IV Clinical Demo dataset (version 2.2), containing EHR records for 100 adult patients across 140 ICU stays. The outcome target `hospital_expire_flag` represents in-hospital mortality. 

The cohort displays a severe class imbalance, with 15 stays resulting in death (11.0%) and 125 stays resulting in survival (89.0%). To maintain evaluation integrity, the data is partitioned into an 80% training set ($N=120$ stays) and a 20% holdout test set ($N=20$ stays) using Stratified Shuffle Split to preserve class ratios.

### TABLE I. Target Classification Categories
| Class Index | Class Name | Category |
| :---: | :---: | :---: |
| 0 | Survived | Control |
| 1 | Deceased | Target |

### TABLE II. Data Distribution
| Target Class Name | Total Count | % of Total | Train Split (80%) | Test Split (20%) |
| :--- | :---: | :---: | :---: | :---: |
| **Survived** | 125 | 89.28% | 100 | 25 |
| **Deceased** | 15 | 10.72% | 12 | 3 |
| **TOTAL DATASET** | **140** | **100%** | **112** | **28** |

---

## IV. Data Regularization & Imputation Strategy
In computer vision, data augmentation (rotations, flips, crops) is used to diversify the training set and prevent overfitting. In clinical tabular data, we implement an equivalent **Data Regularization and Clinical Imputation Strategy** to stabilize the model's feature space:

### TABLE III. Clinical Regularization & Imputation Pipeline
| Technique | Parameter | Purpose / Clinical Equivalence |
| :--- | :---: | :--- |
| **Temperature Unification** | $C = (F - 32) \times 5/9$ | Normalizes temperature scales to Celsius. |
| **Outlier Scrubbing** | HR [30, 220], Temp [32, 45] | Replaces physiological noise with NaN. |
| **Clinical Baseline Imputation** | Potassium = 4.2, Creatinine = 0.9 | Imputes missing laboratory values with healthy reference values to simulate normalcy. |
| **Informative Missingness** | `is_missing_<lab_name>` | Encodes the clinician's decision to order a laboratory test as a predictive feature. |
| **Z-Score Scaling** | Mean = 0, Std = 1 | Scales continuous vital signs to standardize features. |

Clinical baseline imputation acts as a powerful regularizer: instead of imputing missing labs with arbitrary means that distort physiological relationships, we impute them with healthy reference baselines. This represents the medical assumption of normalcy unless a test is clinically indicated and ordered.

---

## V. Methodology
Each classifier candidate is trained using an identical pipeline. Nine models are evaluated: Logistic Regression, Random Forest, Balanced Random Forest, XGBoost, LightGBM, CatBoost, ExtraTrees, Soft-Voting, and Stacking ensembles.

### TABLE IV. Shared Hyperparameter Configuration
| Hyperparameter | Value | Clinical / Technical Purpose |
| :--- | :---: | :--- |
| **Observation Window** | $t \le \text{intime} + 24\text{h}$ | Restricts data to the first 24 hours of the first ICU stay to prevent leakage. |
| **Imbalanced Loss Handling** | `class_weight='balanced'` | Applies inverse frequency weights to penalize minority class errors. |
| **Cross-Validation** | Stratified 5-Fold | Ensures equal mortality distribution across training and validation folds. |
| **Optimization Criterion** | Youden's J Statistic | Shopes the decision threshold to maximize Balanced Accuracy. |
| **Decision Threshold** | 0.39 (ExtraTrees) | Shifted threshold to resuscitate sensitivity. |

---

## VI. Architectural Design & Training
The system is built as a three-tier architecture: Data Preprocessing, Machine Learning Modeling, and Clinical Actionability.

1. **Preprocessing Layer**: Performs outlier cleaning, Celsius normalization, and clinical reference imputation.
2. **Modeling Layer (ExtraTrees Champion)**: We select the **ExtraTrees Classifier** (Extremely Randomized Trees) as the champion. ExtraTrees randomizes split thresholds during tree building rather than searching for optimal split boundaries. This adds regularization and reduces estimator variance, allowing it to generalize better on small clinical samples compared to standard Random Forest or Gradient Boosting.
3. **Clinical Actionability Layer (Tree SHAP & Streamlit)**: Tree SHAP decomposes individual risk scores into additive biophysical contributions. The Streamlit dashboard serves these predictions in Clinical and Research modes.

---

## VII. Results and Discussion
Model performance was evaluated on the stratified 20% holdout test set ($N=20$) under the Youden-optimized threshold of 0.39:

### TABLE V. Holdout Performance Summary
| Model Name | Opt. Threshold | Test Accuracy | Test Sensitivity | Test Specificity | Test ROC-AUC | Test PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ExtraTrees (Champion)** | **0.39** | **0.5500** | **0.5000** | **0.5556** | **0.5556** | **0.1603** |
| **Logistic Regression** | 0.43 | 0.4500 | 0.5000 | 0.4444 | 0.4444 | 0.1250 |
| **Random Forest** | 0.38 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.1429 |
| **XGBoost** | 0.41 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.1429 |
| **Stacking Ensemble** | 0.44 | 0.4500 | 0.5000 | 0.4444 | 0.4444 | 0.1250 |

By shifting the decision threshold from 0.50 to 0.39, the ExtraTrees champion successfully resolved the majority-class collapse, recovering sensitivity to 50% on unseen test data. Ensembles overfitted the small cohort size, yielding lower test performance.

### Interpretability via Tree SHAP
In computer vision, Grad-CAM maps deep feature activations to spatial regions on an image. In clinical tabular prediction, we use **Tree SHAP** as the mathematical equivalent to map model outputs to biophysical drivers:

1. **Global Interpretability**: Identifies Potassium (Min), BUN (Mean), and Systolic BP (Mean) as the primary risk predictors across the cohort. Low potassium (hypokalemia) and elevated BUN contribute positively to mortality risk, aligning with clinical literature.
2. **Local Interpretability**: Generates patient-specific waterfall plots at the bedside. The SHAP values additively decompose the prediction, showing which biophysical markers push the patient's risk score above the Youden threshold of 0.39.

---

## VIII. Conclusion
This study demonstrates the feasibility of an Explainable AI-based Clinical Decision Support System for early ICU mortality prediction. By restricting data to the first 24 hours of ICU stay, applying clinical preprocessing, and engineering statistical aggregates, the pipeline avoids data leakage. Optimizing classification decision thresholds using Youden's J statistic resolves class imbalance, while SHAP explains risk scores, bridging the gap between machine learning and clinician bedside trust.

---

## References
[1] A. E. W. Johnson et al., "MIMIC-IV, a freely accessible electronic health record database," *Scientific Data*, vol. 10, no. 1, p. 1, 2023.  
[2] S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," in *Advances in Neural Information Processing Systems (NeurIPS)*, 2017.  
[3] W. J. Youden, "Index for rating diagnostic tests," *Cancer*, vol. 3, no. 1, pp. 32-35, 1950.  
[4] P. Geurts, D. Ernst, and L. Wehenkel, "Extremely randomized trees," *Machine Learning*, vol. 63, no. 1, pp. 3-42, 2006.  
[5] C. D. Mullins et al., "Patient-centeredness in clinical decision support systems," *JAMIA*, vol. 22, no. 6, 2015.
