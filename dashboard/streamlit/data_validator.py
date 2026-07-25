import re
import pandas as pd
import numpy as np

REQUIRED_MODEL_COLUMNS = [
    "limit_bal", "sex", "education", "marriage", "age",
    "pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6",
    "bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6",
    "pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6"
]

TARGET_COLUMN = "default_payment_next_month"

import re
import pandas as pd


def normalize_column_names(df: pd.DataFrame):
    normalized_df = df.copy()
    column_mapping = {}

    normalized_columns = []

    for column in normalized_df.columns:
        normalized = str(column).strip().lower()

        normalized = re.sub(
            r"[\s\.\-/]+",
            "_",
            normalized,
        )

        normalized = re.sub(r"_+", "_", normalized)
        normalized = normalized.strip("_")

        column_mapping[column] = normalized
        normalized_columns.append(normalized)

    normalized_df.columns = normalized_columns

    return normalized_df, column_mapping

def generate_validation_report(df: pd.DataFrame) -> dict:
    """
    Validates a normalized dataframe and returns a report dictionary.
    """
    errors = []
    warnings = []
    infos = []
    
    # 1. Missing required columns
    missing_required = [c for c in REQUIRED_MODEL_COLUMNS if c not in df.columns]
    if missing_required:
        errors.append({"severity": "Error", "message": f"Missing required columns for model: {', '.join(missing_required)}"})
        
    # 2. Target column
    has_target = TARGET_COLUMN in df.columns
    if not has_target:
        infos.append({"severity": "Info", "message": "Uploaded file lacks target column. Supervised analytics unavailable."})
    else:
        invalid_target = df[~df[TARGET_COLUMN].isin([0, 1, np.nan])].shape[0]
        if invalid_target > 0:
            errors.append({"severity": "Error", "message": f"Target column '{TARGET_COLUMN}' has {invalid_target} invalid values (must be 0 or 1)."})
            
    # 3. Missing values
    total_missing = df.isnull().sum().sum()
    if total_missing > 0:
        cols_with_missing = df.columns[df.isnull().any()].tolist()
        warnings.append({"severity": "Warning", "message": f"Dataset contains {total_missing} missing values across {len(cols_with_missing)} columns."})
        
    # 4. Data Types
    for col in df.columns:
        if col in REQUIRED_MODEL_COLUMNS or col == TARGET_COLUMN:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            invalid_count = numeric_col.isnull().sum() - df[col].isnull().sum()
            if invalid_count > 0:
                errors.append({"severity": "Error", "message": f"Column '{col}' has {invalid_count} invalid non-numeric values."})

    # 5. Duplicates
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        warnings.append({"severity": "Warning", "message": f"Found {dup_count} duplicate rows."})
        
    # Extra columns
    expected_cols = REQUIRED_MODEL_COLUMNS + [TARGET_COLUMN, "id"]
    extra_cols = [c for c in df.columns if c not in expected_cols]
    if extra_cols:
        infos.append({"severity": "Info", "message": f"Extra columns ignored by model: {', '.join(extra_cols[:5])}{'...' if len(extra_cols) > 5 else ''}"})
        
    # Overall Status
    if len(errors) > 0:
        status = "Invalid File"
    elif not has_target:
        status = "Ready for Prediction Only"
    else:
        status = "Ready for Analytics and Prediction"
        
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "missing_count": total_missing,
        "dup_count": dup_count,
        "has_target": has_target
    }

def prepare_uploaded_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares the dataset for analytics and model prediction.
    Assumes df is already normalized and has required columns.
    Generates derived features.
    """
    df = df.copy()
    
    # Safe coercion for required model columns
    for col in REQUIRED_MODEL_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    if TARGET_COLUMN in df.columns:
        df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors='coerce')

    if "id" not in df.columns:
        df.insert(0, "id", range(1, len(df) + 1))
        
    # Create derived features
    bill_cols = ["bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"]
    pay_amt_cols = ["pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6"]
    pay_status_cols = ["pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6"]
    
    df["average_bill_amount"] = df[bill_cols].mean(axis=1)
    df["total_bill_amount"] = df[bill_cols].sum(axis=1)
    df["average_payment_amount"] = df[pay_amt_cols].mean(axis=1)
    df["total_payment_amount"] = df[pay_amt_cols].sum(axis=1)
    
    # Safe division for payment_to_bill_ratio
    df["payment_to_bill_ratio"] = df["total_payment_amount"] / df["total_bill_amount"].replace({0: 1})
    
    df["maximum_delay_months"] = df[pay_status_cols].apply(lambda row: max([v for v in row if v > 0] + [0]), axis=1)
    df["delayed_payment_count"] = df[pay_status_cols].apply(lambda row: sum(1 for v in row if v > 0), axis=1)
    df["has_payment_delay"] = (df["delayed_payment_count"] > 0).astype(int)
    
    df["credit_utilisation_ratio"] = df["total_bill_amount"] / (6 * df["limit_bal"].replace({0: 1}))
    
    # Labels
    df["delay_status"] = df["has_payment_delay"].map({1: "Delayed", 0: "No Delay"})
    if TARGET_COLUMN in df.columns:
        df["default_status"] = df[TARGET_COLUMN].map({1: "Defaulter", 0: "Reliable"})
        
    def categorize_age(age):
        if pd.isna(age): return "Unknown"
        if age < 30: return "20s"
        elif age < 40: return "30s"
        elif age < 50: return "40s"
        elif age < 60: return "50s"
        else: return "60+"
    df["age_group"] = df["age"].apply(categorize_age)
    
    def categorize_credit(limit):
        if pd.isna(limit): return "Unknown"
        if limit <= 50000: return "Low (<=50k)"
        elif limit <= 150000: return "Medium (50k-150k)"
        elif limit <= 300000: return "High (150k-300k)"
        else: return "Very High (>300k)"
    df["credit_limit_group"] = df["limit_bal"].apply(categorize_credit)
    
    df["sex_label"] = df["sex"].map({1: "Male", 2: "Female"}).fillna("Unknown")
    df["education_label"] = df["education"].map({1: "Graduate School", 2: "University", 3: "High School", 4: "Others"}).fillna("Unknown")
    df["marriage_label"] = df["marriage"].map({1: "Married", 2: "Single", 3: "Others"}).fillna("Unknown")
    
    return df
