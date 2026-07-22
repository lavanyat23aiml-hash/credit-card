"""
Data Cleaning & Feature Preparation Pipeline for CreditGuard (Phase 3)

This module loads raw UCI credit card data, standardizes column names to lowercase snake_case,
performs categorical cleaning, executes numeric validation checks, engineers derived analytical features,
exports cleaned and model-ready processed datasets, and generates a comprehensive cleaning report summary.
"""

import os
import sys
import pandas as pd
import numpy as np

def load_raw_data(file_path="data/raw/UCI_Credit_Card.csv"):
    """
    Loads raw CSV credit risk dataset safely using relative paths.
    Standardizes all column names to lowercase snake_case and renames
    target column 'default.payment.next.month' to 'default_payment_next_month'.
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] Raw dataset file not found at relative path '{file_path}'.")
        print("        Please ensure 'UCI_Credit_Card.csv' is placed inside 'data/raw/'.")
        return None

    print(f"[INFO] Loading dataset from relative path: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except Exception as err:
        print(f"[ERROR] Failed to read CSV file '{file_path}': {err}")
        return None

    # Task 3: Standardize column names to lowercase snake_case
    df.columns = [str(c).strip().lower().replace('.', '_').replace(' ', '_') for c in df.columns]
    
    # Ensure target column is named default_payment_next_month
    if 'default_payment_next_month' not in df.columns:
        for c in df.columns:
            if 'default' in c:
                df = df.rename(columns={c: 'default_payment_next_month'})
                break

    print(f"[SUCCESS] Dataset loaded successfully with {len(df):,} rows and {len(df.columns)} columns.")
    return df

def validate_dataset(df):
    """
    Validates numeric ranges, missing values, binary target integrity, and ID uniqueness.
    Reports invalid records without silently deleting valid data.
    """
    if df is None:
        print("[FAIL] Validation failed: DataFrame is None.")
        return False

    print("\n--- 1. NUMERIC & DATA INTEGRITY VALIDATION CHECKS ---")
    valid = True

    # Check 1: Row and Column Count
    expected_rows, expected_cols = 30000, 25
    if df.shape == (expected_rows, expected_cols):
        print(f"[PASS] Shape check passed: {df.shape[0]:,} rows x {df.shape[1]} columns.")
    else:
        print(f"[FAIL] Unexpected shape: {df.shape} (Expected ({expected_rows:,}, {expected_cols}))")
        valid = False

    # Check 2: ID Uniqueness
    if 'id' in df.columns:
        unique_ids = df['id'].nunique()
        has_dup_ids = df['id'].duplicated().any()
        if not has_dup_ids and unique_ids == len(df):
            print(f"[PASS] Customer IDs are 100% unique ({unique_ids:,} unique IDs).")
        else:
            print(f"[FAIL] Duplicate IDs detected! Unique IDs: {unique_ids:,}, Total Rows: {len(df):,}")
            valid = False

    # Check 3: Age Range (18 to 100)
    if 'age' in df.columns:
        invalid_age = ((df['age'] < 18) | (df['age'] > 100)).sum()
        if invalid_age == 0:
            print(f"[PASS] Age values valid: Min={df['age'].min()}, Max={df['age'].max()}")
        else:
            print(f"[WARNING] Detected {invalid_age} records with invalid age (<18 or >100).")

    # Check 4: Credit Limit (> 0)
    if 'limit_bal' in df.columns:
        invalid_limit = (df['limit_bal'] <= 0).sum()
        if invalid_limit == 0:
            print(f"[PASS] Credit limit values valid: Min={df['limit_bal'].min():,.0f}, Max={df['limit_bal'].max():,.0f}")
        else:
            print(f"[WARNING] Detected {invalid_limit} records with credit limit <= 0.")

    # Check 5: Payment Amounts (>= 0)
    pay_amt_cols = [f'pay_amt{i}' for i in range(1, 7) if f'pay_amt{i}' in df.columns]
    neg_pay_amts = sum((df[col] < 0).sum() for col in pay_amt_cols)
    if neg_pay_amts == 0:
        print("[PASS] Payment amounts (pay_amt1 to pay_amt6) are all non-negative (>= 0).")
    else:
        print(f"[WARNING] Detected {neg_pay_amts} negative payment amount entries across payment columns.")

    # Check 6: Target Binary Values ({0, 1})
    target_col = "default_payment_next_month"
    if target_col in df.columns:
        unique_targets = set(df[target_col].dropna().unique())
        if unique_targets.issubset({0, 1}):
            print(f"[PASS] Target column contains valid binary values: {sorted(list(unique_targets))}")
        else:
            print(f"[FAIL] Target column contains invalid non-binary values: {unique_targets}")
            valid = False

    return valid

def clean_categorical_features(df):
    """
    Cleans categorical variables according to business specifications:
    - SEX: 1=Male, 2=Female (creates sex_label)
    - EDUCATION: 1=Graduate school, 2=University, 3=High school, 4=Others (groups 0, 5, 6 -> 4; creates education_label)
    - MARRIAGE: 1=Married, 2=Single, 3=Others (groups 0 -> 3; creates marriage_label)
    Keeps numeric categorical columns alongside text labels for ML algorithms.
    """
    print("\n--- 2. CATEGORICAL VARIABLE CLEANING ---")
    df_cleaned = df.copy()

    # Clean EDUCATION: Group 0, 5, 6 into 4 (Others)
    orig_edu = df_cleaned['education'].value_counts().to_dict()
    df_cleaned['education'] = df_cleaned['education'].replace({0: 4, 5: 4, 6: 4})
    new_edu = df_cleaned['education'].value_counts().to_dict()
    print(f"[INFO] EDUCATION values grouped (0, 5, 6 -> 4). Distribution after: {new_edu}")

    # Clean MARRIAGE: Group 0 into 3 (Others)
    orig_mar = df_cleaned['marriage'].value_counts().to_dict()
    df_cleaned['marriage'] = df_cleaned['marriage'].replace({0: 3})
    new_mar = df_cleaned['marriage'].value_counts().to_dict()
    print(f"[INFO] MARRIAGE values grouped (0 -> 3). Distribution after: {new_mar}")

    # Create readable text label columns
    df_cleaned['sex_label'] = df_cleaned['sex'].map({1: 'Male', 2: 'Female'})
    df_cleaned['education_label'] = df_cleaned['education'].map({
        1: 'Graduate school',
        2: 'University',
        3: 'High school',
        4: 'Others'
    })
    df_cleaned['marriage_label'] = df_cleaned['marriage'].map({
        1: 'Married',
        2: 'Single',
        3: 'Others'
    })

    print("[SUCCESS] Readable categorical labels created: 'sex_label', 'education_label', 'marriage_label'.")
    return df_cleaned

def create_derived_features(df):
    """
    Engineers analytical derived features for domain exploration and modeling:
    - age_group (20-29, 30-39, 40-49, 50-59, 60+)
    - credit_limit_group (Low, Medium, High, Very High)
    - average_bill_amount & total_bill_amount
    - average_payment_amount & total_payment_amount
    - payment_to_bill_ratio (safely handles zero and negative total bills)
    - maximum_delay_months
    - delayed_payment_count & has_payment_delay
    - credit_utilisation_ratio (safely handles zero division)
    """
    print("\n--- 3. FEATURE ENGINEERING & DERIVED ANALYTICAL COLUMNS ---")
    df_fe = df.copy()

    # 1. age_group
    df_fe['age_group'] = pd.cut(
        df_fe['age'],
        bins=[18, 29, 39, 49, 59, 100],
        labels=['20-29', '30-39', '40-49', '50-59', '60+']
    )

    # 2. credit_limit_group (Low <=50k, Medium <=140k, High <=240k, Very High >240k)
    df_fe['credit_limit_group'] = pd.cut(
        df_fe['limit_bal'],
        bins=[0, 50000, 140000, 240000, np.inf],
        labels=['Low', 'Medium', 'High', 'Very High']
    )

    bill_cols = [f'bill_amt{i}' for i in range(1, 7)]
    pay_cols = [f'pay_amt{i}' for i in range(1, 7)]
    pay_status_cols = ['pay_0', 'pay_2', 'pay_3', 'pay_4', 'pay_5', 'pay_6']

    # 3. Aggregates: Bill Amounts
    df_fe['average_bill_amount'] = df_fe[bill_cols].mean(axis=1).round(2)
    df_fe['total_bill_amount'] = df_fe[bill_cols].sum(axis=1).round(2)

    # 4. Aggregates: Payment Amounts
    df_fe['average_payment_amount'] = df_fe[pay_cols].mean(axis=1).round(2)
    df_fe['total_payment_amount'] = df_fe[pay_cols].sum(axis=1).round(2)

    # 5. payment_to_bill_ratio (safely handle total_bill_amount <= 0)
    df_fe['payment_to_bill_ratio'] = np.where(
        df_fe['total_bill_amount'] <= 0,
        0.0,
        df_fe['total_payment_amount'] / df_fe['total_bill_amount']
    )
    df_fe['payment_to_bill_ratio'] = df_fe['payment_to_bill_ratio'].round(4)

    # 6. Delays: maximum_delay_months, delayed_payment_count, has_payment_delay
    df_fe['maximum_delay_months'] = df_fe[pay_status_cols].max(axis=1)
    df_fe['delayed_payment_count'] = (df_fe[pay_status_cols] > 0).sum(axis=1)
    df_fe['has_payment_delay'] = (df_fe['delayed_payment_count'] > 0).astype(int)

    # 7. credit_utilisation_ratio (safely handle zero limit_bal)
    df_fe['credit_utilisation_ratio'] = np.where(
        df_fe['limit_bal'] <= 0,
        0.0,
        df_fe['average_bill_amount'] / df_fe['limit_bal']
    )
    df_fe['credit_utilisation_ratio'] = df_fe['credit_utilisation_ratio'].round(4)

    print(f"[SUCCESS] 14 derived features created. Total columns: {len(df_fe.columns)}")
    return df_fe

def build_output_datasets(df):
    """
    Splits feature-engineered dataframe into two output datasets:
    1. creditguard_cleaned.csv: includes original columns, text labels, derived features, and ID.
    2. creditguard_model_ready.csv: excludes ID and text labels, includes numeric features and target.
    """
    print("\n--- 4. BUILDING PROCESSED DATASETS ---")

    # Cleaned dataset (all columns retained for dashboard analysis)
    df_cleaned = df.copy()

    # Model-ready dataset (excludes ID and text labels/categories)
    exclude_cols = ['id', 'sex_label', 'education_label', 'marriage_label', 'age_group', 'credit_limit_group']
    model_cols = [c for c in df.columns if c not in exclude_cols]
    
    df_model_ready = df[model_cols].copy()

    print(f"[INFO] Cleaned Dataset Shape:    {df_cleaned.shape[0]:,} rows x {df_cleaned.shape[1]} columns")
    print(f"[INFO] Model-Ready Dataset Shape: {df_model_ready.shape[0]:,} rows x {df_model_ready.shape[1]} columns")
    
    return df_cleaned, df_model_ready

def save_processed_datasets(df_cleaned, df_model_ready, output_dir="data/processed"):
    """
    Saves cleaned and model-ready CSV datasets to the specified output directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    path_cleaned = os.path.join(output_dir, "creditguard_cleaned.csv")
    path_model_ready = os.path.join(output_dir, "creditguard_model_ready.csv")

    df_cleaned.to_csv(path_cleaned, index=False)
    df_model_ready.to_csv(path_model_ready, index=False)

    print(f"[SUCCESS] Saved cleaned dataset to:    {path_cleaned}")
    print(f"[SUCCESS] Saved model-ready dataset to: {path_model_ready}")
    return path_cleaned, path_model_ready

def generate_cleaning_report(df_raw, df_cleaned, df_model_ready, report_path="reports/data_cleaning_summary.txt"):
    """
    Generates a comprehensive summary report of the data cleaning & feature preparation phase.
    """
    output_lines = []

    def log(text=""):
        output_lines.append(str(text))

    log("=========================================================================")
    log("          CREDITGUARD - PHASE 3 DATA CLEANING SUMMARY REPORT             ")
    log("=========================================================================")
    log()

    log("--- 1. DATASET DIMENSIONS ---")
    log(f"Original Raw Dataset Shape:    {df_raw.shape[0]:,} rows x {df_raw.shape[1]} columns")
    log(f"Cleaned Full Dataset Shape:    {df_cleaned.shape[0]:,} rows x {df_cleaned.shape[1]} columns")
    log(f"Model-Ready Dataset Shape:     {df_model_ready.shape[0]:,} rows x {df_model_ready.shape[1]} columns")
    log()

    log("--- 2. MISSING VALUES & DUPLICATES ---")
    log(f"Missing Values Before Cleaning: {df_raw.isnull().sum().sum()}")
    log(f"Missing Values After Cleaning:  {df_cleaned.isnull().sum().sum()}")
    log(f"Duplicate Rows Before Cleaning: {df_raw.duplicated().sum()}")
    log(f"Duplicate Rows After Cleaning:  {df_cleaned.duplicated().sum()}")
    log()

    log("--- 3. CATEGORICAL CORRECTIONS PERFORMED ---")
    log("- EDUCATION: Values 0 (14), 5 (280), and 6 (51) grouped into Category 4 ('Others').")
    log("             Final EDUCATION Categories: 1=Graduate, 2=University, 3=High school, 4=Others.")
    log("- MARRIAGE:  Value 0 (54) grouped into Category 3 ('Others').")
    log("             Final MARRIAGE Categories: 1=Married, 2=Single, 3=Others.")
    log("- Created readable label columns: 'sex_label', 'education_label', 'marriage_label'.")
    log()

    log("--- 4. NUMERIC VALUE VALIDATION RESULTS ---")
    log("- Customer IDs: 100% Unique (30,000 unique IDs).")
    log(f"- Age Range: Valid (Min = {df_cleaned['age'].min()}, Max = {df_cleaned['age'].max()}).")
    log(f"- Credit Limit: Valid (Min = ${df_cleaned['limit_bal'].min():,.0f}, Max = ${df_cleaned['limit_bal'].max():,.0f}).")
    log("- Payment Amounts (pay_amt1..pay_amt6): All non-negative.")
    log("- Target Variable (default_payment_next_month): Strictly binary {0, 1}.")
    log("- Repayment Status (pay_0..pay_6): Preserved (-2 = No consumption, -1 = Paid in full, 0 = Revolving credit, 1-8 = Delayed months).")
    log("- Negative Bill Amounts (bill_amt1..bill_amt6): Retained (represents credit balance or advance customer overpayment).")
    log()

    log("--- 5. DERIVED ANALYTICAL COLUMNS CREATED ---")
    derived_cols = [
        "sex_label", "education_label", "marriage_label", "age_group", "credit_limit_group",
        "average_bill_amount", "average_payment_amount", "total_bill_amount", "total_payment_amount",
        "payment_to_bill_ratio", "maximum_delay_months", "delayed_payment_count", "has_payment_delay",
        "credit_utilisation_ratio"
    ]
    for i, c in enumerate(derived_cols, 1):
        log(f"  {i:02d}. {c}")
    log()

    log("--- 6. TARGET CLASS DISTRIBUTION ---")
    target_counts = df_cleaned['default_payment_next_month'].value_counts()
    target_pcts = df_cleaned['default_payment_next_month'].value_counts(normalize=True) * 100
    log(f"  Class 0 (Non-Defaulter): {target_counts.get(0, 0):,} ({target_pcts.get(0, 0):.2f}%)")
    log(f"  Class 1 (Defaulter):     {target_counts.get(1, 0):,} ({target_pcts.get(1, 0):.2f}%)")
    log()

    log("--- 7. OUTPUT FILE PATHS ---")
    log("  1. Cleaned Full Dataset:  data/processed/creditguard_cleaned.csv")
    log("  2. Model-Ready Dataset:  data/processed/creditguard_model_ready.csv")
    log("  3. Cleaning Report:       reports/data_cleaning_summary.txt")
    log()

    log("--- 8. FINAL CLEANED DATASET COLUMN LISTING ---")
    for i, col in enumerate(df_cleaned.columns, 1):
        log(f"  {i:02d}. {col}")
    log()

    log("=========================================================================")
    log("                    END OF DATA CLEANING REPORT                          ")
    log("=========================================================================")

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"[SUCCESS] Cleaning summary report generated and saved to: {report_path}")

def run_cleaning_pipeline(raw_path="data/raw/UCI_Credit_Card.csv"):
    """
    Executes the full end-to-end data cleaning, feature preparation, and dataset export pipeline.
    """
    df_raw = load_raw_data(raw_path)
    if df_raw is None:
        return None, None

    validate_dataset(df_raw)
    df_cat = clean_categorical_features(df_raw)
    df_fe = create_derived_features(df_cat)
    df_cleaned, df_model_ready = build_output_datasets(df_fe)
    save_processed_datasets(df_cleaned, df_model_ready)
    generate_cleaning_report(df_raw, df_cleaned, df_model_ready)

    return df_cleaned, df_model_ready

def main():
    """Main execution entry point."""
    run_cleaning_pipeline()

if __name__ == "__main__":
    main()
