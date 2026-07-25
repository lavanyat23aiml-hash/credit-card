import pytest
import pandas as pd
import numpy as np
from dashboard.streamlit.data_validator import (
    normalize_column_names,
    generate_validation_report,
    prepare_uploaded_dataset,
    REQUIRED_MODEL_COLUMNS,
    TARGET_COLUMN
)

def get_valid_row():
    row = {col: 10000 if "amt" in col or "bal" in col else 1 for col in REQUIRED_MODEL_COLUMNS}
    row[TARGET_COLUMN] = 0
    return row

def test_normalize_column_names():
    df = pd.DataFrame({"LIMIT BAL": [1], "PAY-0": [1], "default payment next month": [1]})
    mapping = normalize_column_names(df)
    
    assert "limit_bal" in df.columns
    assert "pay_0" in df.columns
    assert "default_payment_next_month" in df.columns
    assert mapping["LIMIT BAL"] == "limit_bal"

def test_generate_validation_report_valid():
    df = pd.DataFrame([get_valid_row(), get_valid_row()])
    # Make rows unique so no duplicate warning
    df.loc[1, "age"] = 35 
    
    report = generate_validation_report(df)
    assert report["status"] == "Ready for Analytics and Prediction"
    assert len(report["errors"]) == 0
    assert report["dup_count"] == 0

def test_generate_validation_report_missing_target():
    row = get_valid_row()
    del row[TARGET_COLUMN]
    df = pd.DataFrame([row])
    
    report = generate_validation_report(df)
    assert report["status"] == "Ready for Prediction Only"
    assert len(report["errors"]) == 0
    assert not report["has_target"]

def test_generate_validation_report_invalid_target():
    row = get_valid_row()
    row[TARGET_COLUMN] = 5 # Invalid
    df = pd.DataFrame([row])
    
    report = generate_validation_report(df)
    assert report["status"] == "Invalid File"
    assert any("Target column" in e["message"] for e in report["errors"])

def test_generate_validation_report_missing_columns():
    row = get_valid_row()
    del row["age"]
    df = pd.DataFrame([row])
    
    report = generate_validation_report(df)
    assert report["status"] == "Invalid File"
    assert any("Missing required columns" in e["message"] for e in report["errors"])

def test_generate_validation_report_duplicates():
    df = pd.DataFrame([get_valid_row(), get_valid_row()])
    
    report = generate_validation_report(df)
    assert report["dup_count"] == 1
    assert any("duplicate" in w["message"].lower() for w in report["warnings"])

def test_prepare_uploaded_dataset():
    df = pd.DataFrame([get_valid_row()])
    prepared = prepare_uploaded_dataset(df)
    
    assert "id" in prepared.columns
    assert "average_bill_amount" in prepared.columns
    assert "total_bill_amount" in prepared.columns
    assert "credit_utilisation_ratio" in prepared.columns
    assert "age_group" in prepared.columns
    assert "delay_status" in prepared.columns
    if TARGET_COLUMN in df.columns:
        assert "default_status" in prepared.columns
