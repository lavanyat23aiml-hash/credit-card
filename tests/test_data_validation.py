"""
Tests for dashboard.streamlit.data_validation
"""

import pytest
import pandas as pd
import numpy as np
from dashboard.streamlit.data_validation import (
    validate_uploaded_dataset,
    get_missing_required_columns,
    validate_column_types,
    detect_data_issues,
    get_data_quality_report,
    CRITICAL_COLUMNS,
    OPTIONAL_COLUMNS,
    QUALITY_PENALTIES,
)

# Helper function to generate a fully populated valid dataset row
def _base_valid_row():
    return {
        "id": 1,
        "limit_bal": 100000,
        "sex": 1,
        "education": 2,
        "marriage": 1,
        "age": 35,
        "pay_0": 0,
        "pay_2": 0,
        "pay_3": 0,
        "pay_4": 0,
        "pay_5": 0,
        "pay_6": 0,
        "bill_amt1": 15000,
        "bill_amt2": 14000,
        "bill_amt3": 13000,
        "bill_amt4": 12000,
        "bill_amt5": 11000,
        "bill_amt6": 10000,
        "pay_amt1": 2000,
        "pay_amt2": 2000,
        "pay_amt3": 2000,
        "pay_amt4": 2000,
        "pay_amt5": 2000,
        "pay_amt6": 2000,
        "default_payment_next_month": 0,
    }

def _make_df(n=5, overrides=None):
    rows = []
    for i in range(n):
        row = _base_valid_row()
        row["id"] = i + 1
        if overrides:
            row.update(overrides)
        rows.append(row)
    return pd.DataFrame(rows)

# 1. Valid Dataset Test
def test_valid_dataset_passes():
    df = _make_df()
    report = validate_uploaded_dataset(df)
    
    assert report["status"] == "pass"
    assert report["quality_score"] == 100
    assert len(report["errors"]) == 0
    assert len(report["warnings"]) == 0

# 2. Missing Optional Columns Test
def test_missing_optional_columns_warning():
    df = _make_df()
    # Drop some optional columns
    df = df.drop(columns=["pay_amt5", "pay_amt6", "default_payment_next_month"])
    
    report = validate_uploaded_dataset(df)
    assert report["status"] == "warning"
    assert "default_payment_next_month" in report["optional_missing_columns"]
    assert "pay_amt5" in report["optional_missing_columns"]
    # Check that score is deducted: 100 - (3 * 3) = 91
    assert report["quality_score"] == 91
    assert len(report["errors"]) == 0

# 3. Missing Critical Columns Test
def test_missing_critical_columns_error():
    df = _make_df()
    # Drop critical columns
    df = df.drop(columns=["limit_bal", "age"])
    
    report = validate_uploaded_dataset(df)
    assert report["status"] == "error"
    assert "limit_bal" in report["critical_missing_columns"]
    assert "age" in report["critical_missing_columns"]
    assert len(report["errors"]) > 0

# 4. Empty File Handling Test
def test_empty_dataset_error():
    df = pd.DataFrame()
    report = validate_uploaded_dataset(df)
    
    assert report["status"] == "error"
    assert report["quality_score"] == 0
    assert len(report["errors"]) > 0

# 5. Duplicate Detection Test
def test_duplicate_records_deduction():
    df = _make_df(n=5)
    # Add a duplicate row
    dup_row = pd.DataFrame([_base_valid_row()])
    dup_row["id"] = 1 # Same ID
    df = pd.concat([df, dup_row], ignore_index=True)
    
    report = validate_uploaded_dataset(df)
    assert "Found 1 duplicate customer records (exact duplicate rows)." in report["warnings"]
    # 10 points deduction for duplicates + 5 for duplicate IDs = 15 points deduction
    assert report["quality_score"] == 85

# 6. Invalid Numeric Values Test
def test_invalid_numeric_values_handling():
    df = _make_df()
    df["limit_bal"] = df["limit_bal"].astype(object)
    # Insert string in a numeric column
    df.loc[0, "limit_bal"] = "invalid_string"
    
    report = validate_uploaded_dataset(df)
    # Because limit_bal is critical, non-numeric values in it should raise an error
    assert report["status"] == "error"
    assert any("cannot be converted to numbers" in err for err in report["errors"])
    
    # Now check a string in optional column (should trigger warning, not error)
    df_opt = _make_df()
    df_opt["pay_amt1"] = df_opt["pay_amt1"].astype(object)
    df_opt.loc[0, "pay_amt1"] = "invalid_string"
    report_opt = validate_uploaded_dataset(df_opt)
    assert report_opt["status"] == "warning"
    assert any("cannot be converted to numbers" in warn for warn in report_opt["warnings"])

# 7. Negative Financial Values Test
def test_negative_financial_values():
    df = _make_df(overrides={"limit_bal": -50000, "pay_amt1": -100, "bill_amt1": -200})
    
    report = validate_uploaded_dataset(df)
    # Check that they are flagged in warnings
    assert any("negative credit limit" in warn for warn in report["warnings"])
    assert any("negative payment amount" in warn for warn in report["warnings"])
    assert any("negative billing amounts" in warn for warn in report["warnings"])
    
    # Deductions: 10 (neg limit) + 10 (neg payment) + 5 (neg bill) = 25
    assert report["quality_score"] == 75

# 8. Partial Dataset Execution Test (No crash)
def test_partial_dataset_no_crash():
    # Construct a highly partial dataset (only containing base columns)
    df = pd.DataFrame({
        "limit_bal": [50000, 100000],
        "sex": [1, 2],
        "education": [2, 3],
        "marriage": [1, 2],
        "age": [25, 45],
        "pay_0": [0, 2]
    })
    
    # Validation should run without crashing
    report = validate_uploaded_dataset(df)
    assert report["status"] == "warning"
    assert len(report["critical_missing_columns"]) == 0
    # Optional columns are missing
    assert len(report["optional_missing_columns"]) > 0
