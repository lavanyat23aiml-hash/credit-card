"""
CreditGuard — Dataset Validation Framework.
Provides schema, format, type, ranges, duplicates, and outliers check for uploaded datasets.
"""

import numpy as np
import pandas as pd

# Centralized column lists
CRITICAL_COLUMNS = ["limit_bal", "sex", "education", "marriage", "age", "pay_0"]
OPTIONAL_COLUMNS = [
    "pay_2", "pay_3", "pay_4", "pay_5", "pay_6",
    "bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6",
    "pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6",
    "default_payment_next_month", "id"
]

# Scoring deduction rules
QUALITY_PENALTIES = {
    "missing_optional_column": 3,
    "missing_values": 5,
    "duplicates": 10,
    "negative_limit": 10,
    "negative_pay_amt": 10,
    "negative_bill_amt": 5,
    "type_errors": 5,
    "outliers": 5,
    "invalid_id": 5,
}

def get_missing_required_columns(df: pd.DataFrame) -> dict:
    """Detect missing critical and optional columns."""
    critical_missing = [c for c in CRITICAL_COLUMNS if c not in df.columns]
    optional_missing = [c for c in OPTIONAL_COLUMNS if c not in df.columns]
    return {
        "critical_missing": critical_missing,
        "optional_missing": optional_missing,
    }

def validate_column_types(df: pd.DataFrame) -> dict:
    """Ensure numeric values exist in numeric columns."""
    errors = []
    warnings = []
    type_issues = []
    
    numeric_check_cols = [c for c in CRITICAL_COLUMNS + OPTIONAL_COLUMNS if c in df.columns and c != "id" and c != "default_payment_next_month"]
    
    for col in numeric_check_cols:
        coerced = pd.to_numeric(df[col], errors='coerce')
        original_not_null = df[col].notnull()
        coerced_null = coerced.isnull()
        invalid_count = (original_not_null & coerced_null).sum()
        
        if invalid_count > 0:
            msg = f"Column '{col}' has {invalid_count} values that cannot be converted to numbers."
            if col in CRITICAL_COLUMNS:
                errors.append(msg)
            else:
                warnings.append(msg)
            type_issues.append(col)
            
    return {
        "errors": errors,
        "warnings": warnings,
        "type_issues": type_issues
    }

def detect_data_issues(df: pd.DataFrame) -> dict:
    """Detect duplicate, missing, negative financial values, outliers, and invalid IDs."""
    warnings = []
    errors = []
    deductions = []
    penalties = 0
    
    # 1. Empty dataset check
    if df.empty:
        errors.append("The uploaded dataset is empty (0 rows).")
        return {
            "errors": errors,
            "warnings": warnings,
            "deductions": ["Dataset is completely empty (100 points deducted)"],
            "penalties": 100,
        }
        
    # 2. Missing values check
    missing_counts = df.isnull().sum()
    total_missing = missing_counts.sum()
    if total_missing > 0:
        missing_cols = missing_counts[missing_counts > 0].index.tolist()
        warnings.append(f"Found {total_missing} missing values across columns: {', '.join(missing_cols)}.")
        penalties += QUALITY_PENALTIES["missing_values"]
        deductions.append(f"{QUALITY_PENALTIES['missing_values']} points deducted for missing values in dataset.")
        
    # 3. Duplicate rows check
    dup_rows = df.duplicated().sum()
    if dup_rows > 0:
        warnings.append(f"Found {dup_rows} duplicate customer records (exact duplicate rows).")
        penalties += QUALITY_PENALTIES["duplicates"]
        deductions.append(f"{QUALITY_PENALTIES['duplicates']} points deducted due to {dup_rows} duplicate rows.")

    # 4. ID check (if ID is present)
    if "id" in df.columns:
        dup_ids = df["id"].duplicated().sum()
        if dup_ids > 0:
            warnings.append(f"Found {dup_ids} duplicate customer IDs.")
            penalties += QUALITY_PENALTIES["invalid_id"]
            deductions.append(f"{QUALITY_PENALTIES['invalid_id']} points deducted for duplicate IDs.")
            
        id_numeric = pd.to_numeric(df["id"], errors='coerce')
        invalid_ids = id_numeric.isnull().sum()
        if invalid_ids > 0:
            warnings.append(f"Found {invalid_ids} invalid non-numeric customer IDs.")
            if "invalid_id" not in deductions:
                penalties += QUALITY_PENALTIES["invalid_id"]
                deductions.append(f"{QUALITY_PENALTIES['invalid_id']} points deducted for invalid non-numeric IDs.")
                
    # 5. Financial Validation (Negative limits, negative payments, negative bills)
    if "limit_bal" in df.columns:
        limits = pd.to_numeric(df["limit_bal"], errors='coerce')
        neg_limits = (limits < 0).sum()
        if neg_limits > 0:
            warnings.append(f"Found {neg_limits} rows with negative credit limit (limit_bal).")
            penalties += QUALITY_PENALTIES["negative_limit"]
            deductions.append(f"{QUALITY_PENALTIES['negative_limit']} points deducted for negative credit limits.")
            
    pay_amt_cols = [c for c in df.columns if c.startswith("pay_amt")]
    if pay_amt_cols:
        neg_payments = 0
        for col in pay_amt_cols:
            payments = pd.to_numeric(df[col], errors='coerce')
            neg_payments += (payments < 0).sum()
        if neg_payments > 0:
            warnings.append(f"Found {neg_payments} negative payment amount values across billing cycles.")
            penalties += QUALITY_PENALTIES["negative_pay_amt"]
            deductions.append(f"{QUALITY_PENALTIES['negative_pay_amt']} points deducted for negative payments.")
            
    bill_amt_cols = [c for c in df.columns if c.startswith("bill_amt")]
    if bill_amt_cols:
        neg_bills = 0
        for col in bill_amt_cols:
            bills = pd.to_numeric(df[col], errors='coerce')
            neg_bills += (bills < 0).sum()
        if neg_bills > 0:
            warnings.append(f"Found {neg_bills} negative billing amounts (could indicate credit balance/overpayment).")
            penalties += QUALITY_PENALTIES["negative_bill_amt"]
            deductions.append(f"{QUALITY_PENALTIES['negative_bill_amt']} points deducted for negative bill amounts.")

    # 6. Statistical Outliers (robust 3x IQR check)
    if "limit_bal" in df.columns:
        limits = pd.to_numeric(df["limit_bal"], errors='coerce').dropna()
        if len(limits) >= 5:
            q1 = limits.quantile(0.25)
            q3 = limits.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outliers_count = ((limits < (q1 - 3 * iqr)) | (limits > (q3 + 3 * iqr))).sum()
                if outliers_count > 0:
                    warnings.append(f"Found {outliers_count} statistical outlier(s) in credit limit (limit_bal) using robust 3x IQR check.")
                    penalties += QUALITY_PENALTIES["outliers"]
                    deductions.append(f"{QUALITY_PENALTIES['outliers']} points deducted for extreme credit outliers.")
                    
    return {
        "errors": errors,
        "warnings": warnings,
        "deductions": deductions,
        "penalties": penalties,
    }

def get_data_quality_report(df: pd.DataFrame) -> dict:
    """Generate complete validation and data quality analysis report."""
    errors = []
    warnings = []
    deductions = []
    penalties = 0
    
    if df is None or df.empty:
        errors.append("Dataset is empty or invalid.")
        return {
            "status": "error",
            "missing_columns": [],
            "critical_missing_columns": [],
            "optional_missing_columns": [],
            "warnings": [],
            "errors": errors,
            "quality_score": 0,
            "deductions": ["Dataset is empty (100 points deducted)"],
            "details": {}
        }
        
    missing = get_missing_required_columns(df)
    critical_missing = missing["critical_missing"]
    optional_missing = missing["optional_missing"]
    
    if critical_missing:
        errors.append(f"Missing critical columns required for system core functions: {', '.join(critical_missing)}")
        penalties += 100
        deductions.append("Missing critical columns (100 points deducted)")
    
    if optional_missing:
        warnings.append(f"Missing optional analytical columns: {', '.join(optional_missing)}")
        col_penalty = len(optional_missing) * QUALITY_PENALTIES["missing_optional_column"]
        penalties += col_penalty
        deductions.append(f"{col_penalty} points deducted for {len(optional_missing)} missing optional columns.")
        
    type_report = validate_column_types(df)
    errors.extend(type_report["errors"])
    warnings.extend(type_report["warnings"])
    if type_report["type_issues"]:
        type_penalty = len(type_report["type_issues"]) * QUALITY_PENALTIES["type_errors"]
        penalties += type_penalty
        deductions.append(f"{type_penalty} points deducted for type mismatch issues in columns: {', '.join(type_report['type_issues'])}.")
        
    issues_report = detect_data_issues(df)
    errors.extend(issues_report["errors"])
    warnings.extend(issues_report["warnings"])
    penalties += issues_report["penalties"]
    deductions.extend(issues_report["deductions"])
    
    quality_score = max(0, 100 - penalties)
    
    if len(errors) > 0:
        status = "error"
    elif len(warnings) > 0 or quality_score < 90:
        status = "warning"
    else:
        status = "pass"
        
    return {
        "status": status,
        "missing_columns": critical_missing + optional_missing,
        "critical_missing_columns": critical_missing,
        "optional_missing_columns": optional_missing,
        "warnings": warnings,
        "errors": errors,
        "quality_score": int(quality_score),
        "deductions": deductions,
        "details": {
            "total_rows": len(df),
            "total_cols": len(df.columns)
        }
    }

def validate_uploaded_dataset(df: pd.DataFrame) -> dict:
    """Main validation entry point for uploaded datasets."""
    return get_data_quality_report(df)
