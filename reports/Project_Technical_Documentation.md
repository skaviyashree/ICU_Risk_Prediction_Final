# Project Technical Documentation: Explainable AI-Based Clinical Decision Support System (CDSS) for ICU Mortality Prediction

> **Document Class**: System Technical Dossier & Developer Reference Manual  
> **Status**: COMPLETE (Phase II Overhaul Audited)  
> **Database Source**: MIMIC-IV Clinical Demo Database v2.2  
> **Programming Stack**: Python, Streamlit, Scikit-Learn, SHAP, ReportLab, Matplotlib  
> **Deployment Target**: Streamlit Community Cloud (Proof-of-Concept)  
> **Live Application URL**: [https://icu-risk-prediction-csgt.streamlit.app](https://icu-risk-prediction-csgt.streamlit.app)  

---

## Table of Contents
1. [1. Executive Summary](#1-executive-summary)
2. [2. Project Motivation](#2-project-motivation)
3. [3. Problem Statement](#3-problem-statement)
4. [4. Objectives](#4-objectives)
5. [5. Scope](#5-scope)
6. [6. Dataset Description](#6-dataset-description)
7. [7. Dataset Statistics](#7-dataset-statistics)
8. [8. Data Dictionary](#8-data-dictionary)
9. [9. Clinical Variables Used](#9-clinical-variables-used)
10. [10. Feature Selection Strategy](#10-feature-selection-strategy)
11. [11. Feature Engineering Pipeline](#11-feature-engineering-pipeline)
12. [12. Data Cleaning](#12-data-cleaning)
13. [13. Missing Value Handling](#13-missing-value-handling)
14. [14. Outlier Detection](#14-outlier-detection)
15. [15. Scaling](#15-scaling)
16. [16. Feature Aggregation](#16-feature-aggregation)
17. [17. Complete ML Pipeline](#17-complete-ml-pipeline)
18. [18. Cross Validation Strategy](#18-cross-validation-strategy)
19. [19. Threshold Optimization](#19-threshold-optimization)
20. [20. Champion Model Selection](#20-champion-model-selection)
21. [21. Explainability using SHAP](#21-explainability-using-shap)
22. [22. Clinical Recommendation Engine](#22-clinical-recommendation-engine)
23. [23. Dashboard Architecture](#23-dashboard-architecture)
24. [24. Streamlit UI Explanation](#24-streamlit-ui-explanation)
25. [25. PDF Report Generator](#25-pdf-report-generator)
26. [26. Folder Structure](#26-folder-structure)
27. [27. File-by-file Explanation](#27-file-by-file-explanation)
28. [28. Module Dependency Diagram](#28-module-dependency-diagram)
29. [29. Execution Flow](#29-execution-flow)
30. [30. System Workflow](#30-system-workflow)
31. [31. Block Diagram Explanation](#31-block-diagram-explanation)
32. [32. Deployment Process](#32-deployment-process)
33. [33. GitHub Repository Structure](#33-github-repository-structure)
34. [34. Streamlit Cloud Deployment](#34-streamlit-cloud-deployment)
35. [35. Software Requirements](#35-software-requirements)
36. [36. Hardware Requirements](#36-hardware-requirements)
37. [37. Libraries Used](#37-libraries-used)
38. [38. Limitations](#38-limitations)
39. [39. Future Improvements](#39-future-improvements)
40. [40. Complete Technical Conclusion](#40-complete-technical-conclusion)

---

## 1. Executive Summary
This technical documentation dossier outlines the development, mathematical validation, and clinical deployment of an Explainable Artificial Intelligence (XAI) bedside Clinical Decision Support System (CDSS) for early in-hospital mortality risk prediction in intensive care units. Developed as a feasibility study utilizing the publicly available MIMIC-IV Clinical Demo database (100 adult patients, 140 ICU stays, 11% mortality rate), the pipeline implements a leak-free temporal framework. This framework restricts all bedside vital signs and laboratory feature extractions strictly to the first 24 hours of a patient's first ICU admission. The machine learning engine evaluates nine classifier candidates, deploying a highly regularized ExtraTrees Classifier as the champion model. By optimizing the classification decision boundary using Youden's J statistic on out-of-fold cross-validation predictions, we shift the threshold from 0.50 to 0.39, resuscitating model sensitivity to 50.00% and specificity to 55.56% on unseen test data. Bedside interpretability is provided via a Tree SHAP engine and a Streamlit web application, allowing physicians to audit risk drivers dynamically and generate signed A4 Patient Chart PDFs at the bedside.

---

## 2. Project Motivation
Critical care medicine is characterized by a high volume of time-sensitive patient data. In modern ICUs, continuous monitoring devices produce streams of vital sign telemetries (heart rate, respiratory rate, blood pressure, oxygen saturation). This data density, coupled with intermittent laboratory blood panels, often leads to cognitive overload and alarm fatigue for ICU clinicians. Alarm fatigue—where clinicians desensitize to warning signals due to high rates of false-positive alarms—poses a major threat to patient safety, leading to delayed responses to actual clinical deterioration. Furthermore, standard EHR machine learning models frequently suffer from data leakage by extracting features recorded right before death or discharge, rendering them useless for early intervention. The motivation of this project is to build an early-warning CDSS that operates strictly on the initial 24 hours of ICU stay to detect high-risk states early, while providing transparent explanations using game-theoretic SHAP values to bridge the gap between machine learning and clinician bedside trust.

---

## 3. Problem Statement
Given a patient's demographics, continuous bedside vital sign telemetry, and laboratory panel measurements recorded strictly within the first 24 hours of their first ICU stay, the objective is to predict the probability of in-hospital mortality (defined by the binary label `hospital_expire_flag`). 

The prediction must be made under three main constraints:
1. **Clinical Actionability**: The model must operate on early, non-leaked observations to enable life-saving interventions.
2. **Imbalance Resilience**: The system must handle a severe class imbalance (11.0% mortality) without collapsing into predicting survival for all cases (majority-class collapse, which yields 0% recall).
3. **Transparency**: The predictions must be fully explainable at the bedside to allow immediate physician audit.

---

## 4. Objectives
The primary engineering and clinical objectives of the project are:
1. Ingest raw de-identified EHR tables from the MIMIC-IV Clinical Demo database and isolate a clean cohort of adult stays.
2. Implement a clinical preprocessing pipeline to convert temperature units, clean sensor noise, and flag outliers.
3. Design a feature engineering pipeline to slice the 24-hour observation window and compute 6 distinct statistical aggregates per concept.
4. Implement clinical imputation utilizing healthy reference baselines to prevent data skewing.
5. Train, optimize, and cross-validate nine candidate classifiers under Stratified 5-Fold Cross-Validation.
6. Optimize classification decision thresholds using Youden's J statistic on out-of-fold predictions to handle class imbalance.
7. Integrate a Tree SHAP explainability engine to deconstruct risk scores into biophysical risk drivers.
8. Deconstruct predictions into natural language narratives and deploy the CDSS as a Streamlit web application with vector PDF registry chart exports.

---

## 5. Scope
This project is developed strictly as a proof-of-concept feasibility study using the MIMIC-IV Clinical Demo dataset (100 patients, 140 stays). It establishes a baseline MLOps framework for early risk prediction and bedside interpretability. The system has not undergone clinical trials, clinical validation, or real-world hospital deployment, and must not be used for actual clinical diagnostic decisions. The scope covers data ingestion, offline stratified model training, threshold sweeps, SHAP explainability, and Streamlit Community Cloud hosting.

---

## 6. Dataset Description
The project uses the MIMIC-IV Clinical Demo dataset (version 2.2), a publicly available de-identified EHR database containing clinical data from Beth Israel Deaconess Medical Center. The primary tables ingested are:
* **`patients`**: Demographic anchor age and gender.
* **`admissions`**: Hospital admission details, race, insurance plan, marital status, and the `hospital_expire_flag` target.
* **`icustays`**: ICU stay timestamps (intime, outtime), care unit designations, and stay IDs.
* **`chartevents`**: Bedside vitals (668,862 records).
* **`labevents`**: Clinical laboratory blood draws (107,727 records).

---

## 7. Dataset Statistics
The cohort consists of 100 adult patients across 140 ICU stays. The outcome target `hospital_expire_flag` displays a severe class imbalance, with 15 stays resulting in in-hospital mortality (11.0%) and 125 stays resulting in survival (89.0%). The average age at admission is 64.92 years. Demographics show a predominant white population (78%), with emergency admissions representing the majority of cases. Continuous telemetry data contains 668,862 bedside vitals and 107,727 lab measurements, presenting high data density.

---

## 8. Data Dictionary
* **`subject_id`** (int): Unique identifier for each patient.
* **`hadm_id`** (int): Unique identifier for each hospital admission.
* **`stay_id`** (int): Unique identifier for each ICU stay.
* **`age`** (float): Patient age at ICU admission (anchor_age + year of intime - anchor_year).
* **`gender`** (int): Biological sex (1 = Male, 0 = Female).
* **`race`** (string): Self-reported ethnicity/race.
* **`admission_type`** (string): Source category of hospital admission.
* **`insurance`** (string): Primary insurance plan type (Medicare, Medicaid, Other).
* **`marital_status`** (string): Marital status of the patient.
* **`hospital_expire_flag`** (int): Target label (1 = Deceased in hospital, 0 = Survived).

---

## 9. Clinical Variables Used
The model utilizes 9 core biophysical markers selected for clinical significance:
1. **Age** (demographic risk)
2. **Heart Rate Std** (vital sign volatility)
3. **SpO2 Mean** (oxygenation baseline)
4. **Systolic BP Mean** (cardiovascular baseline)
5. **MAP Min** (lowest Mean Arterial Pressure, shock risk)
6. **Temperature Mean** (thermoregulation baseline, sepsis marker)
7. **BUN Mean** (Blood Urea Nitrogen, renal function)
8. **Creatinine Latest** (kidney injury progression)
9. **Potassium Min** (cardiac muscle stability, arrhythmia risk)

---

## 10. Feature Selection Strategy
Training 107 raw features on a small dataset (100 patients) leads to high-variance overfitting ($p > N$ problem). To prevent this, we drop the SMOTE oversampler and constrain the pipeline's feature space to 9 clinically validated biomarkers. This regularizes the decision boundary, reducing model variance and ensuring stable out-of-sample generalization on the holdout test set.

---

## 11. Feature Engineering Pipeline
The pipeline is executed inside the 24-hour observation window ($t \le \text{intime} + 24\text{h}$). For each vital and lab concept, it extracts 6 statistical aggregates: Mean, Minimum, Maximum, Standard Deviation, Latest (last value recorded), and Trend (Latest - First). Laboratory parameters also track missingness indicator flags (`is_missing_<lab_name>`) to record the clinical decision of ordering a test.

---

## 12. Data Cleaning
Data cleaning handles unit discrepancies and sensor noise. Fahrenheit temperature readings (item ID 223761) are normalized to Celsius: $C = (F - 32) \times 5/9$, and merged with Celsius records (item ID 223762). Telemetry observations falling outside plausible bounds (e.g. Heart Rate < 30 or > 220 bpm) are set to NaN, allowing them to be imputed during feature engineering.

---

## 13. Missing Value Handling
Missing vital signs are imputed using global cohort medians. Missing laboratory values (which are ordered intermittently due to informative missingness) are imputed using healthy reference baselines (Potassium = 4.2 mEq/L, BUN = 14.0 mg/dL, Creatinine = 0.9 mg/dL) using the `CLINICAL_REF_LABS` dictionary. This represents the medical assumption of normalcy unless observed otherwise, avoiding bias.

---

## 14. Outlier Detection
Outlier detection relies on clinical limits defined in the `OUTLIER_BOUNDS` dictionary. Telemetry monitors generate noise (e.g. displaced sensors showing SpO2 of 0%). Removing these extreme values and setting them to NaN ensures that the downstream statistical aggregates (especially Standard Deviation and Trend) are not corrupted by artifacts.

---

## 15. Scaling
Features are scaled using `StandardScaler()` within a `ColumnTransformer`. This normalizes the 9 clinical biomarkers to have a mean of 0 and standard deviation of 1. Scaling is critical for linear models (Logistic Regression) and prevents variables with larger absolute scales (e.g. Systolic BP) from dominating the distance calculations in ensemble algorithms.

---

## 16. Feature Aggregation
Feature aggregation compresses continuous vital sign and lab measurements over 24 hours into 6 static aggregates. The minimum value captures acute decompensations (bradycardia, hypoxia), maximum captures peak stress (hypertensive crisis, fever), standard deviation captures volatility, and trend captures the patient's direction of recovery or decline. This yields a structured feature matrix of 107 columns prior to feature selection.

---

## 17. Complete ML Pipeline
The pipeline is implemented using `sklearn` and `imblearn`. It comprises a preprocessor `ColumnTransformer` (which applies `StandardScaler` to the 9 selected features and drops the remaining columns) and a classifier. Nine candidates are evaluated: Logistic Regression, Random Forest, Balanced Random Forest, XGBoost, LightGBM, CatBoost, ExtraTrees, Soft-Voting, and Stacking ensembles.

---

## 18. Cross Validation Strategy
The evaluation uses Stratified 5-Fold Cross-Validation. Splitting is stratified by the target label `hospital_expire_flag`, ensuring that the 11% deceased-to-survived ratio is maintained in both training and validation folds. This prevents optimistic biases and ensures stable evaluation on imbalanced data.

---

## 19. Threshold Optimization
Standard classifiers predict survival for all patients on imbalanced data using a 0.5 threshold. To resolve this, we sweep thresholds (0.01 to 0.99) on out-of-fold validation sets to find the cutoff maximizing Youden's J Statistic ($J = \text{Sensitivity} + \text{Specificity} - 1$, equivalent to Balanced Accuracy). The optimal thresholds are averaged across folds to obtain a robust global threshold of 0.39 for the ExtraTrees model.

---

## 20. Champion Model Selection
Models are ranked by their holdout Clinical Composite Score ($\text{PR-AUC} + \text{ROC-AUC} + \text{Recall}$). The ExtraTrees Classifier (`ext_trees`) with an optimized threshold of 0.39 was selected as the champion model. It achieved holdout Accuracy = 0.5500, Sensitivity = 0.5000, Specificity = 0.5556, ROC-AUC = 0.5556, and PR-AUC = 0.1603, outperforming stacking ensembles which overfit the small sample size.

---

## 21. Explainability using SHAP
We use Tree SHAP to provide global and local explainability. Global interpretability identifies Potassium (Min) and BUN (Mean) as the primary risk predictors. Local interpretability generates patient-specific waterfall plots, deconstructing risk scores into biophysical drivers and compiling them into natural-language risk narratives.

---

## 22. Clinical Recommendation Engine
Calculated probabilities are mapped to clinical alerts: Low Risk (<5%), Moderate Risk (<15%), High Risk (<40%), and Critical Risk (>=40%). Each risk band is mapped to rule-based clinical recommendations (e.g. triggering a Rapid Response Team bedside review if risk is >= 40% or Systolic BP is < 90 mmHg).

---

## 23. Dashboard Architecture
The Streamlit bedside dashboard follows a clean, responsive layout. It utilizes cached data and model loading to prevent lag, displays patient demographics, calculated risk levels, alert banners, local SHAP waterfalls, bedside trend charts, rule-based clinical guides, and exports vector A4 PDFs.

---

## 24. Streamlit UI Explanation
* **Clinical Mode**: Features Demo Patient Registry Lookup (dropdown of stays) and Bedside Physiological Slider Builder (sliders for manually adjusting vital/lab metrics). Displays alert cards, SHAP narratives, and PDF exports.
* **Research Mode**: Displays performance leaderboards, model galleries (ROC/confusion matrix curves), global SHAP swarm plots, and cohort correlation heatmaps.

---

## 25. PDF Report Generator
The `pdf_generator.py` module uses matplotlib's vector engine to compile a vector A4 PDF Bedside Chart registry export. The PDF contains patient demographics, risk assessment scales, SHAP narratives, clinical advisories, and physician signature fields, ready for clinical registry filing.

---

## 26. Folder Structure
* `data/`: raw CSVs, processed feature matrices, serialized models (`best_model.joblib`).
* `figures/`: candidate model sweeps, ROC/PR curves, post-retraining figures.
* `reports/`: master handbooks, model comparison reports, ieee conference papers.
* `src/`: `data_ingestion.py`, `preprocessing.py`, `feature_engineering.py`, `train.py`, `explainability.py`, `pdf_generator.py`, `config.py`.
* `app/`: `app.py`, `utils.py`.
* `Screenshots/`: clinical/research UI pngs.

---

## 27. File-by-file Explanation
* `config.py`: Configuration path definitions, clinical mappings, outlier boundaries, and hyperparameters.
* `data_ingestion.py`: Ingests raw zipped CSVs, selects first stays, filters age >= 18, and merges admissions.
* `preprocessing.py`: Handles Fahrenheit to Celsius conversion and sets vital outliers to NaN.
* `feature_engineering.py`: Slices the 24-hour observation window, computes 6 aggregates, handles missingness, and imputes labs with healthy references.
* `train.py`: Scales selected clinical markers, runs Stratified 5-Fold CV, searches Youden's J threshold, and saves the champion ExtraTrees pipeline.
* `explainability.py`: Initializes the SHAP engine, translates raw columns to clinical labels, and generates bedside waterfall plots and clinician NLP narratives.
* `pdf_generator.py`: Generates the vector A4 PDF bedside report.
* `app.py & utils.py`: Streamlit dashboard frontend and CSS styles.

---

## 28. Module Dependency Diagram
* `config.py` is imported by all backend modules.
* `data_ingestion.py` -> `preprocessing.py` -> `feature_engineering.py` -> `train.py`.
* `train.py` serializes `best_model.joblib`.
* `explainability.py` imports `best_model.joblib` and `config.py`.
* `pdf_generator.py` imports `config.py`.
* `app.py` imports `explainability.py`, `pdf_generator.py`, `utils.py`, and `best_model.joblib`.

---

## 29. Execution Flow
The pipeline is executed end-to-end using `run_pipeline.py`: Ingestion loads raw files -> Preprocessing cleans vitals -> Feature Engineering aggregates over 24 hours -> Training scales, cross-validates, searches thresholds, and saves `best_model.joblib` -> Explainability fits the background SHAP explainer -> Figures are saved.

---

## 30. System Workflow
At the bedside: The clinician selects an ICU stay or adjusts sliders -> Streamlit calls the ExtraTrees model to evaluate probability -> SHAP computes local contributions -> Rule-based advisories are triggered -> Matplotlib compiles the vector PDF chart -> The physician signs the chart.

---

## 31. Block Diagram Explanation
The system block diagram (Fig. 1) represents the 3-layer workflow: (1) Data Ingestion and Multimodal Preprocessing; (2) Predictive Machine Learning Engine (ExtraTrees champion); and (3) Clinical Actionability Tier (Streamlit/PDF export), illustrating how EHR data is transformed into explainable bedside advisories.

![Fig. 1. Architecture of the proposed Explainable AI-based Clinical Decision Support System for ICU mortality prediction.](file:///d:/ICU_Risk_Prediction_AI/figures/publication/system_architecture_diagram.png)
*Figure 3: Overhauled horizontal architecture diagram of the clinical ML pipeline.*

---

## 32. Deployment Process
The system is deployed on Streamlit Community Cloud. The GitHub repository contains all code, dependencies, and serialized models. Streamlit Community Cloud pulls the repository, installs dependencies, and serves the application on a public URL.

---

## 33. GitHub Repository Structure
The repository contains: `app/` (`app.py`, `utils.py`), `src/` (modules, `config.py`), `data/` (raw/processed/models), `figures/` (curves, rankings), `reports/` (handbooks, papers), `screenshots/` (UI pngs), `requirements.txt`, and `run_pipeline.py`.

---

## 34. Streamlit Cloud Deployment
The Streamlit Community Cloud deployment is configured to automatically fetch the master branch of the repository, set up the Python environment, install packages from `requirements.txt`, and run `app/app.py` as the entrypoint served on the public URL.

---

## 35. Software Requirements
* Python 3.10+
* Operating System: Windows/Linux/MacOS
* Web Browser: Chrome, Firefox, or Safari for dashboard access
* Git: for repository version control

---

## 36. Hardware Requirements
* CPU: Dual-Core 2.0 GHz or higher (Quad-Core recommended for SHAP background fits)
* RAM: 8 GB or higher (16 GB recommended for loading full chartevents in memory)
* Disk Space: 500 MB (MIMIC demo files are small, full database requires >100 GB)

---

## 37. Libraries Used
* **`pandas`** (v2.0.0+): clinical data frame manipulation
* **`numpy`** (v1.22.0+): mathematical operations
* **`scikit-learn`** (v1.2.0+): ML pipelines and scaling
* **`imbalanced-learn`** (v0.10.0+): class weighting
* **`xgboost`/`lightgbm`/`catboost`**: candidate classifiers
* **`shap`** (v0.41.0+): explainability engine
* **`reportlab`** (v4.5.1+): portrait master handbook PDF compilation
* **`python-docx`** (v1.2.0+): Word document formatting

---

## 38. Limitations
The primary limitation is the sample size constraint (100 patients, 140 stays) of the MIMIC-IV Clinical Demo database. This causes high variance and limits model discriminative power (ROC-AUC = 0.5556). Furthermore, the application is a proof-of-concept feasibility study and has not undergone clinical validation.

---

## 39. Future Improvements
Future improvements will focus on: (1) Scale: training on the full MIMIC-IV database (>300,000 stays); (2) Waveforms: utilizing continuous temporal models (RNNs/Transformers) on high-frequency vital sign streams; (3) Integration: streaming bedside data via HL7 FHIR APIs; (4) Qualitative NLP: extracting notes embeddings using ClinicalBERT.

---

## 40. Complete Technical Conclusion
In conclusion, this project establishes the feasibility of an Explainable AI-based bedside CDSS for early ICU mortality prediction. By restricting observations to the first 24 hours of ICU stay, applying clinical preprocessing, and engineering 6 multimodal aggregates, the pipeline avoids data leakage. Optimizing classification decision thresholds using Youden's J statistic resolves class imbalance, while SHAP explains risk scores, bridging the gap between machine learning and clinician bedside trust.
