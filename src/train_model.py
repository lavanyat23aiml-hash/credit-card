import pandas as pd
import numpy as np
import os
import sys
import json
import joblib
import matplotlib.pyplot as plt
import matplotlib as mpl

from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV, RandomizedSearchCV, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, precision_score, 
                             recall_score, f1_score, roc_auc_score, average_precision_score, 
                             confusion_matrix, classification_report, roc_curve, precision_recall_curve)
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE

# ---------------------------------------------------------
# Configuration and Styling
# ---------------------------------------------------------
PRIMARY_COLOR = '#1F77B4' # Corporate Blue
HIGHLIGHT_COLOR = '#FF7F0E' # Corporate Orange

plt.style.use('default')
mpl.rcParams['axes.facecolor'] = '#F8F9FA'
mpl.rcParams['figure.facecolor'] = '#FFFFFF'
mpl.rcParams['font.size'] = 11

def create_directories():
    dirs = ['models', 'reports/model', 'images/model']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"[INFO] Ensured directory exists: {d}")

def validate_data(df):
    if df.empty:
        raise ValueError("Dataset is empty.")
    if 'default_payment_next_month' not in df.columns:
        raise ValueError("Target column 'default_payment_next_month' missing.")
    if not set(df['default_payment_next_month'].unique()).issubset({0, 1}):
        raise ValueError("Target contains non-binary values.")
    if df.isnull().sum().sum() > 0:
        raise ValueError("Missing values found in dataset.")
    if 'id' in df.columns.str.lower():
        raise ValueError("ID column detected, must be removed.")
    
    # Check for text columns
    text_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(text_cols) > 0:
        raise ValueError(f"Text/Category columns found: {text_cols}. Must be numeric.")

def plot_confusion_matrix(y_true, y_pred, title, filename):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.matshow(cm, cmap='Blues')
    plt.colorbar(cax)
    
    for (i, j), z in np.ndenumerate(cm):
        ax.text(j, i, f"{z}", ha='center', va='center', 
                color='white' if z > (cm.max()/2) else 'black', fontweight='bold')
                
    ax.set_title(title, pad=20)
    ax.set_xlabel('Predicted Label (0=Non-Default, 1=Default)')
    ax.set_ylabel('True Label')
    ax.set_xticks([0,1])
    ax.set_yticks([0,1])
    plt.savefig(f"images/model/{filename}", dpi=300, bbox_inches='tight')
    plt.close()

def plot_roc_curves(models_dict, X_test, y_test, filename):
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, model in models_dict.items():
        if hasattr(model, "predict_proba"):
            y_probs = model.predict_proba(X_test)[:, 1]
            fpr, tpr, _ = roc_curve(y_test, y_probs)
            auc = roc_auc_score(y_test, y_probs)
            ax.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})")
            
    ax.plot([0, 1], [0, 1], 'k--', label="Random")
    ax.set_title("5. ROC Curves for Evaluated Models")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend(loc="lower right", fontsize=9)
    plt.savefig(f"images/model/{filename}", dpi=300, bbox_inches='tight')
    plt.close()

def plot_pr_curves(models_dict, X_test, y_test, filename):
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, model in models_dict.items():
        if hasattr(model, "predict_proba"):
            y_probs = model.predict_proba(X_test)[:, 1]
            precision, recall, _ = precision_recall_curve(y_test, y_probs)
            ap = average_precision_score(y_test, y_probs)
            ax.plot(recall, precision, label=f"{name} (AP={ap:.3f})")
            
    ax.set_title("6. Precision-Recall Curves")
    ax.set_xlabel("Recall (True Positive Rate)")
    ax.set_ylabel("Precision")
    ax.legend(loc="lower left", fontsize=9)
    plt.savefig(f"images/model/{filename}", dpi=300, bbox_inches='tight')
    plt.close()

def evaluate_model(name, model, X_test, y_test, cost_fn=5, cost_fp=1):
    y_pred = model.predict(X_test)
    y_probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred
    
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    acc = accuracy_score(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_probs)
    ap = average_precision_score(y_test, y_probs)
    
    cost = (fn * cost_fn) + (fp * cost_fp)
    
    return {
        'model_name': name,
        'accuracy': round(acc, 4),
        'balanced_accuracy': round(bal_acc, 4),
        'precision_class_1': round(prec, 4),
        'recall_class_1': round(rec, 4),
        'f1_class_1': round(f1, 4),
        'roc_auc': round(auc, 4),
        'average_precision': round(ap, 4),
        'true_negatives': tn,
        'false_positives': fp,
        'false_negatives': fn,
        'true_positives': tp,
        'business_cost_illustrative': cost
    }

def build_models():
    models = {}
    
    # Model 1: Baseline LR
    models['M1_LR_Baseline'] = ImbPipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(random_state=42, max_iter=1000))
    ])
    
    # Model 2: LR Weighted
    models['M2_LR_Weighted'] = ImbPipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000))
    ])
    
    # Model 3: DT Weighted
    models['M3_DT_Weighted'] = ImbPipeline([
        ('scaler', StandardScaler()),
        ('classifier', DecisionTreeClassifier(class_weight='balanced', random_state=42))
    ])
    
    # Model 4: RF Weighted
    models['M4_RF_Weighted'] = ImbPipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(class_weight='balanced', random_state=42))
    ])
    
    # Model 5: SMOTE + LR
    models['M5_SMOTE_LR'] = ImbPipeline([
        ('scaler', StandardScaler()),
        ('smote', SMOTE(random_state=42)),
        ('classifier', LogisticRegression(random_state=42, max_iter=1000))
    ])
    
    # Model 6: SMOTE + RF
    models['M6_SMOTE_RF'] = ImbPipeline([
        ('scaler', StandardScaler()),
        ('smote', SMOTE(random_state=42)),
        ('classifier', RandomForestClassifier(random_state=42))
    ])
    
    return models

def tune_models(X_train, y_train):
    print("[INFO] Tuning Logistic Regression (Weighted)...")
    lr_pipe = ImbPipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000))
    ])
    lr_param_grid = {
        'classifier__C': [0.01, 0.1, 1, 10],
        'classifier__solver': ['liblinear', 'lbfgs'],
        'classifier__penalty': ['l2']
    }
    cv_strat = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    lr_grid = GridSearchCV(lr_pipe, lr_param_grid, cv=cv_strat, scoring='f1', n_jobs=-1)
    lr_grid.fit(X_train, y_train)
    
    print("[INFO] Tuning Random Forest (Weighted) with RandomizedSearchCV...")
    rf_pipe = ImbPipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(class_weight='balanced', random_state=42))
    ])
    rf_param_dist = {
        'classifier__n_estimators': [100, 200, 300],
        'classifier__max_depth': [5, 10, 15, 20, None],
        'classifier__min_samples_split': [2, 5, 10],
        'classifier__min_samples_leaf': [1, 2, 4],
        'classifier__max_features': ['sqrt', 'log2']
    }
    rf_rand = RandomizedSearchCV(rf_pipe, rf_param_dist, n_iter=20, cv=cv_strat, scoring='f1', n_jobs=-1, random_state=42)
    rf_rand.fit(X_train, y_train)
    
    return {'Tuned_LR_Weighted': lr_grid.best_estimator_, 'Tuned_RF_Weighted': rf_rand.best_estimator_}

def optimize_threshold(model, X_train, y_train, cost_fn=5, cost_fp=1):
    print("[INFO] Optimising threshold via out-of-fold predictions...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Get out of fold probabilities to prevent leakage
    y_probs_oof = cross_val_predict(model, X_train, y_train, cv=cv, method='predict_proba', n_jobs=-1)[:, 1]
    
    thresholds = np.arange(0.1, 0.91, 0.05)
    results = []
    
    for th in thresholds:
        y_pred = (y_probs_oof >= th).astype(int)
        cm = confusion_matrix(y_train, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        prec = precision_score(y_train, y_pred, zero_division=0)
        rec = recall_score(y_train, y_pred)
        f1 = f1_score(y_train, y_pred)
        bal_acc = balanced_accuracy_score(y_train, y_pred)
        spec = tn / (tn + fp)
        cost = (fn * cost_fn) + (fp * cost_fp)
        
        results.append({
            'threshold': th,
            'precision': prec,
            'recall': rec,
            'f1': f1,
            'specificity': spec,
            'balanced_accuracy': bal_acc,
            'business_cost': cost,
            'false_negatives': fn,
            'false_positives': fp
        })
        
    df_th = pd.DataFrame(results)
    df_th.to_csv('reports/model/threshold_analysis.csv', index=False)
    
    # Plot Threshold vs Prec/Rec
    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(df_th['threshold'], df_th['precision'], label='Precision', color=PRIMARY_COLOR)
    ax.plot(df_th['threshold'], df_th['recall'], label='Recall', color=HIGHLIGHT_COLOR)
    ax.set_title("7. Threshold vs Precision and Recall")
    ax.set_xlabel("Threshold")
    ax.set_ylabel("Score")
    ax.legend()
    plt.savefig('images/model/threshold_vs_prec_rec.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Plot Threshold vs F1
    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(df_th['threshold'], df_th['f1'], label='F1-Score', color='purple')
    ax.set_title("8. Threshold vs F1-Score")
    ax.set_xlabel("Threshold")
    ax.set_ylabel("F1-Score")
    ax.legend()
    plt.savefig('images/model/threshold_vs_f1.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Find best threshold based on business cost
    best_row = df_th.loc[df_th['business_cost'].idxmin()]
    best_th = best_row['threshold']
    print(f"[SUCCESS] Optimal threshold selected: {best_th:.2f} (Cost: {best_row['business_cost']})")
    
    return best_th, df_th

def main():
    print("[INFO] Starting Phase 6: Machine Learning Pipeline...")
    create_directories()
    
    df = pd.read_csv('data/processed/creditguard_model_ready.csv')
    validate_data(df)
    
    print(f"[INFO] Dataset shape: {df.shape}")
    print(f"[INFO] Feature count: {df.shape[1] - 1}")
    dist = df['default_payment_next_month'].value_counts(normalize=True) * 100
    print(f"[INFO] Target distribution:\n{dist}")
    
    X = df.drop(columns=['default_payment_next_month'])
    y = df['default_payment_next_month']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train base models
    models = build_models()
    trained_models = {}
    for name, pipeline in models.items():
        print(f"[INFO] Training {name}...")
        pipeline.fit(X_train, y_train)
        trained_models[name] = pipeline
        
    # SMOTE visualization
    smote = SMOTE(random_state=42)
    X_res, y_res = smote.fit_resample(X_train, y_train)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].bar(['0', '1'], y_train.value_counts().values, color=[PRIMARY_COLOR, HIGHLIGHT_COLOR])
    ax[0].set_title("Before SMOTE")
    ax[1].bar(['0', '1'], y_res.value_counts().values, color=[PRIMARY_COLOR, HIGHLIGHT_COLOR])
    ax[1].set_title("After SMOTE")
    plt.suptitle("11. Class Distribution Before and After SMOTE")
    plt.savefig('images/model/smote_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
        
    # Tune models
    tuned_models = tune_models(X_train, y_train)
    trained_models.update(tuned_models)
    
    # Evaluate all
    results = []
    for name, model in trained_models.items():
        res = evaluate_model(name, model, X_test, y_test)
        results.append(res)
        
    df_results = pd.DataFrame(results).sort_values(by='business_cost_illustrative', ascending=True)
    df_results.to_csv('reports/model/model_comparison.csv', index=False)
    
    plot_roc_curves(trained_models, X_test, y_test, "roc_curves.png")
    plot_pr_curves(trained_models, X_test, y_test, "pr_curves.png")
    
    # Metric comparison plot
    df_plot = df_results.set_index('model_name')[['f1_class_1', 'roc_auc', 'recall_class_1']]
    df_plot.plot(kind='bar', figsize=(10, 6), colormap='viridis')
    plt.title("1. Model Metric Comparison")
    plt.ylabel("Score")
    plt.xticks(rotation=45, ha='right')
    plt.savefig('images/model/metric_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Cost comparison plot
    fig, ax = plt.subplots(figsize=(10, 5))
    df_results.set_index('model_name')['business_cost_illustrative'].plot(kind='bar', color=HIGHLIGHT_COLOR, ax=ax)
    ax.set_title("12. Illustrative Business Cost by Model")
    ax.set_ylabel("Total Cost (Lower is better)")
    plt.xticks(rotation=45, ha='right')
    plt.savefig('images/model/business_cost_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    plot_confusion_matrix(y_test, trained_models['M1_LR_Baseline'].predict(X_test), "2. Confusion Matrix (Baseline LR)", "cm_baseline.png")
    
    # Select best model (Random Forest Tuned is generally best for complex non-linear limits)
    best_model_name = 'Tuned_RF_Weighted'
    best_model = trained_models[best_model_name]
    
    # Threshold Optimization
    best_th, _ = optimize_threshold(best_model, X_train, y_train)
    
    # Evaluate final threshold on TEST set
    y_probs_test = best_model.predict_proba(X_test)[:, 1]
    y_pred_def = best_model.predict(X_test)
    y_pred_opt = (y_probs_test >= best_th).astype(int)
    
    plot_confusion_matrix(y_test, y_pred_def, f"3. Confusion Matrix (Final Model @ 0.5)", "cm_final_default.png")
    plot_confusion_matrix(y_test, y_pred_opt, f"4. Confusion Matrix (Final Model @ {best_th:.2f})", "cm_final_optimised.png")
    
    # Feature Importance (RF)
    rf_clf = best_model.named_steps['classifier']
    importances = rf_clf.feature_importances_
    df_imp = pd.DataFrame({'Feature': X.columns, 'Importance': importances}).sort_values(by='Importance', ascending=False)
    df_imp.to_csv('reports/model/feature_importance.csv', index=False)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    df_imp.head(15).plot(kind='barh', x='Feature', y='Importance', ax=ax, color=PRIMARY_COLOR, legend=False)
    ax.invert_yaxis()
    ax.set_title("9. Top 15 Feature Importances (Final Model)")
    plt.savefig('images/model/feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Logistic Coefs
    lr_clf = trained_models['Tuned_LR_Weighted'].named_steps['classifier']
    coefs = lr_clf.coef_[0]
    df_coef = pd.DataFrame({'Feature': X.columns, 'Coefficient': coefs}).sort_values(by='Coefficient', ascending=False)
    df_coef.to_csv('reports/model/logistic_coefficients.csv', index=False)
    
    # Persist Final Model
    print("[INFO] Saving final pipeline and metadata...")
    joblib.dump(best_model, 'models/creditguard_final_pipeline.joblib')
    
    metadata = {
        'model_name': best_model_name,
        'feature_names': list(X.columns),
        'target_column': 'default_payment_next_month',
        'selected_threshold': float(best_th),
        'training_row_count': len(X_train),
        'test_row_count': len(X_test),
        'illustrative_false_positive_cost': 1,
        'illustrative_false_negative_cost': 5,
        'test_metrics_at_opt_threshold': {
            'accuracy': accuracy_score(y_test, y_pred_opt),
            'recall': recall_score(y_test, y_pred_opt),
            'precision': precision_score(y_test, y_pred_opt, zero_division=0),
            'f1': f1_score(y_test, y_pred_opt)
        }
    }
    with open('models/creditguard_model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print("[SUCCESS] Phase 6 completed successfully.")

if __name__ == "__main__":
    main()
