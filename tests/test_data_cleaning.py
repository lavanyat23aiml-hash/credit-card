"""
Unit Tests for CreditGuard Data Cleaning & Feature Preparation Pipeline (Phase 3)
"""

import os
import sys
import pytest
import pandas as pd

# Add src folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from data_cleaning import load_raw_data, clean_categorical_features, create_derived_features, build_output_datasets

@pytest.fixture(scope="module")
def processed_data():
    """Fixture that loads and processes datasets once for all tests."""
    raw_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "raw", "UCI_Credit_Card.csv"))
    df_raw = load_raw_data(raw_path)
    df_cat = clean_categorical_features(df_raw)
    df_fe = create_derived_features(df_cat)
    df_cleaned, df_model_ready = build_output_datasets(df_fe)
    return df_cleaned, df_model_ready

def test_expected_row_count(processed_data):
    """Test that cleaned dataset contains exactly 30,000 rows."""
    df_cleaned, df_model_ready = processed_data
    assert len(df_cleaned) == 30000
    assert len(df_model_ready) == 30000

def test_target_values_are_binary(processed_data):
    """Test that target column default_payment_next_month contains only 0 and 1."""
    df_cleaned, df_model_ready = processed_data
    unique_targets = set(df_cleaned['default_payment_next_month'].unique())
    assert unique_targets.issubset({0, 1})

def test_ids_are_unique(processed_data):
    """Test that IDs in cleaned dataset are 100% unique."""
    df_cleaned, _ = processed_data
    assert 'id' in df_cleaned.columns
    assert df_cleaned['id'].nunique() == len(df_cleaned)
    assert not df_cleaned['id'].duplicated().any()

def test_no_missing_values(processed_data):
    """Test that required columns contain no missing (null) values."""
    df_cleaned, df_model_ready = processed_data
    assert df_cleaned.isnull().sum().sum() == 0
    assert df_model_ready.isnull().sum().sum() == 0

def test_corrected_education_values(processed_data):
    """Test that corrected education values are strictly within {1, 2, 3, 4}."""
    df_cleaned, _ = processed_data
    edu_values = set(df_cleaned['education'].unique())
    assert edu_values.issubset({1, 2, 3, 4})

def test_corrected_marriage_values(processed_data):
    """Test that corrected marriage values are strictly within {1, 2, 3}."""
    df_cleaned, _ = processed_data
    marriage_values = set(df_cleaned['marriage'].unique())
    assert marriage_values.issubset({1, 2, 3})

def test_derived_columns_exist(processed_data):
    """Test that all specified derived analytical columns exist in cleaned dataset."""
    df_cleaned, _ = processed_data
    expected_derived = [
        'sex_label', 'education_label', 'marriage_label', 'age_group', 'credit_limit_group',
        'average_bill_amount', 'average_payment_amount', 'total_bill_amount', 'total_payment_amount',
        'payment_to_bill_ratio', 'maximum_delay_months', 'delayed_payment_count', 'has_payment_delay',
        'credit_utilisation_ratio'
    ]
    for col in expected_derived:
        assert col in df_cleaned.columns, f"Missing derived column: {col}"

def test_model_ready_no_id(processed_data):
    """Test that model-ready dataset excludes customer ID and text label columns."""
    _, df_model_ready = processed_data
    assert 'id' not in df_model_ready.columns
    assert 'sex_label' not in df_model_ready.columns
    assert 'education_label' not in df_model_ready.columns
    assert 'marriage_label' not in df_model_ready.columns

def test_model_ready_contains_target(processed_data):
    """Test that model-ready dataset contains the target column default_payment_next_month."""
    _, df_model_ready = processed_data
    assert 'default_payment_next_month' in df_model_ready.columns
