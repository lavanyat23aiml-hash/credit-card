# CreditGuard Machine Learning Model Report

## 1. Executive Summary
This report outlines the development of the CreditGuard machine learning pipeline. Due to a heavy class imbalance (22.12% defaulters), traditional accuracy metrics were avoided. The objective was to minimize the illustrative business cost (Cost of False Negative = 5, Cost of False Positive = 1). The final selected model, a **Tuned Random Forest with Class Weighting**, successfully balances precision and recall, minimizing total business costs by applying an optimized probability threshold.

## 2. Modelling Objective
To build a highly reliable credit-default prediction model that identifies high-risk customers while controlling the unnecessary rejection of reliable ones, utilizing class-imbalance techniques and cost-sensitive learning.

## 3. Dataset and Target
- **Dataset:** `data/processed/creditguard_model_ready.csv`
- **Total Records:** 30,000
- **Target Variable:** `default_payment_next_month` (1 = Defaulter, 0 = Non-Defaulter)
- **Target Imbalance:** 77.88% Non-Defaulters vs 22.12% Defaulters.

## 4. Train-Test Strategy & Leakage Prevention
- **Split:** 80% Training / 20% Testing with `stratify=y` to preserve the 22% default rate across both subsets.
- **Leakage Prevention:** Utilizing `imblearn.pipeline.Pipeline`, data scaling (`StandardScaler`) and synthetic over-sampling (`SMOTE`) were applied strictly inside the cross-validation folds. The 20% Test set remained entirely untouched throughout hyperparameter tuning and threshold selection.

## 5. Models Evaluated
1. **Logistic Regression (Baseline):** No weighting or resampling.
2. **Logistic Regression (Weighted):** `class_weight='balanced'`
3. **Decision Tree (Weighted):** `class_weight='balanced'`
4. **Random Forest (Weighted):** `class_weight='balanced'`
5. **SMOTE + Logistic Regression:** Synthetic minority over-sampling.
6. **SMOTE + Random Forest:** Synthetic minority over-sampling.

## 6. Tuning Methodology
- **Logistic Regression:** Tuned via `GridSearchCV` over 5 Stratified Folds, focusing on regularization parameter `C`.
- **Random Forest:** Tuned via `RandomizedSearchCV` (20 iterations) over 5 Stratified Folds, optimizing `n_estimators`, `max_depth`, `min_samples_split`, `min_samples_leaf`, and `max_features`.
- **Primary Optimization Metric:** F1-score for Class 1 (Defaulters).

## 7. Threshold Optimisation
Because the default `0.5` probability threshold is rarely optimal for imbalanced datasets:
- **Strategy:** Extracted out-of-fold (OOF) predicted probabilities using `cross_val_predict` on the training set to prevent test-set bias.
- **Search:** Scanned thresholds from `0.1` to `0.9`.
- **Selection:** Selected the threshold that yielded the absolute lowest illustrative Business Cost.

## 8. Business-Cost Assumptions
To simulate a real-world banking environment, costs were applied to misclassifications:
- **False Negative (Missed Defaulter):** Cost = 5
- **False Positive (Rejected Good Customer):** Cost = 1
*(Note: These are purely illustrative assumptions, not actual financial costs).*

## 9. Final Model Selection
- **Selected Model:** Random Forest (Class Weighted and Tuned)
- **Justification:** Random Forest models inherently handle the complex, non-linear boundaries in demographic and financial data better than Logistic Regression. Coupled with class weighting and threshold optimization, it provided the best balance of Recall for defaulters and F1-score while maintaining reasonable computational deployment requirements.

## 10. Important Features
Feature importance was extracted directly from the tuned Random Forest. Unsurprisingly, `pay_0` (repayment status in the most recent month) and engineered metrics like `has_payment_delay` and `credit_utilisation_ratio` dominated the predictive power.

## 11. Limitations & Ethical Considerations
- **Limitations:** The business cost formula assumes a static penalty. In reality, a false negative on a £500,000 credit limit is vastly more expensive than on a £10,000 limit.
- **Ethical Considerations:** Demographic features (Age, Sex, Marriage, Education) were left in the model for the sake of the analysis, but depending on regional banking regulations (e.g., UK FCA, US ECOA), deploying models based on protected demographics is often strictly prohibited.

## 12. Deployment Preparation
The final `Pipeline` object (including the `StandardScaler` and `RandomForestClassifier`) has been serialized to `models/creditguard_final_pipeline.joblib`. The accompanying optimized threshold and input specifications are saved in `models/creditguard_model_metadata.json`. A new utility helper `predict_default_risk()` has been added to `src/utils.py` for seamless integration into the upcoming Streamlit user interface.
