"""
Tests for dashboard.streamlit.fraud_indicators
"""

import pytest
import pandas as pd
import numpy as np
from dashboard.streamlit.fraud_indicators import (
    validate_indicator_columns,
    calculate_credit_utilisation_indicator,
    calculate_delay_indicator,
    calculate_long_delay_indicator,
    calculate_low_repayment_indicator,
    calculate_zero_payment_indicator,
    calculate_bill_spike_indicator,
    calculate_large_exposure_indicator,
    calculate_inconsistent_payment_indicator,
    calculate_outlier_indicator,
    calculate_fraud_risk_score,
    assign_fraud_risk_level,
    generate_customer_indicator_reasons,
    generate_indicator_summary,
    run_fraud_indicators,
    INDICATOR_BASE_COLUMNS,
    FRAUD_RULES,
    _ensure_derived,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────
def _base_row(**overrides):
    """Return a single-row dict with all base + derived columns at safe defaults."""
    row = {
        "id": 1, "limit_bal": 100000, "sex": 1, "education": 2, "marriage": 1, "age": 35,
        "pay_0": 0, "pay_2": 0, "pay_3": 0, "pay_4": 0, "pay_5": 0, "pay_6": 0,
        "bill_amt1": 20000, "bill_amt2": 20000, "bill_amt3": 20000,
        "bill_amt4": 20000, "bill_amt5": 20000, "bill_amt6": 20000,
        "pay_amt1": 5000, "pay_amt2": 5000, "pay_amt3": 5000,
        "pay_amt4": 5000, "pay_amt5": 5000, "pay_amt6": 5000,
    }
    row.update(overrides)
    return row


def _make_df(rows=None, n=1, **overrides):
    if rows:
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame([_base_row(**overrides) for _ in range(n)])
    return _ensure_derived(df)


# ─── Column Validation ───────────────────────────────────────────────────────
def test_validate_indicator_columns_all_present():
    df = _make_df()
    result = validate_indicator_columns(df)
    assert result["can_run"] is True
    assert len(result["missing_base"]) == 0


def test_validate_indicator_columns_missing():
    df = pd.DataFrame({"id": [1], "limit_bal": [100000]})
    result = validate_indicator_columns(df)
    assert result["can_run"] is False
    assert len(result["missing_base"]) > 0


# ─── High Utilisation ────────────────────────────────────────────────────────
def test_high_utilisation_flag_high():
    df = _make_df(credit_utilisation_ratio=0.95)
    # Override with explicit value
    df["credit_utilisation_ratio"] = 0.95
    flags = calculate_credit_utilisation_indicator(df)
    assert flags.iloc[0] == 2


def test_high_utilisation_flag_moderate():
    df = _make_df()
    df["credit_utilisation_ratio"] = 0.80
    flags = calculate_credit_utilisation_indicator(df)
    assert flags.iloc[0] == 1


def test_high_utilisation_flag_low():
    df = _make_df()
    df["credit_utilisation_ratio"] = 0.30
    flags = calculate_credit_utilisation_indicator(df)
    assert flags.iloc[0] == 0


# ─── Repeated Delay ──────────────────────────────────────────────────────────
def test_repeated_delay_flag_high():
    df = _make_df()
    df["delayed_payment_count"] = 5
    flags = calculate_delay_indicator(df)
    assert flags.iloc[0] == 2


def test_repeated_delay_flag_moderate():
    df = _make_df()
    df["delayed_payment_count"] = 2
    flags = calculate_delay_indicator(df)
    assert flags.iloc[0] == 1


def test_repeated_delay_flag_none():
    df = _make_df()
    df["delayed_payment_count"] = 0
    flags = calculate_delay_indicator(df)
    assert flags.iloc[0] == 0


# ─── Long Delay ──────────────────────────────────────────────────────────────
def test_long_delay_flag_high():
    df = _make_df()
    df["maximum_delay_months"] = 5
    flags = calculate_long_delay_indicator(df)
    assert flags.iloc[0] == 2


def test_long_delay_flag_moderate():
    df = _make_df()
    df["maximum_delay_months"] = 2
    flags = calculate_long_delay_indicator(df)
    assert flags.iloc[0] == 1


# ─── Low Repayment ───────────────────────────────────────────────────────────
def test_low_repayment_flag_high():
    df = _make_df()
    df["payment_to_bill_ratio"] = 0.05
    df["total_bill_amount"] = 100000
    flags = calculate_low_repayment_indicator(df)
    assert flags.iloc[0] == 2


def test_low_repayment_flag_moderate():
    df = _make_df()
    df["payment_to_bill_ratio"] = 0.15
    df["total_bill_amount"] = 100000
    flags = calculate_low_repayment_indicator(df)
    assert flags.iloc[0] == 1


def test_low_repayment_flag_zero_bill():
    """When total bill is zero, should not flag."""
    df = _make_df()
    df["payment_to_bill_ratio"] = 0.0
    df["total_bill_amount"] = 0
    flags = calculate_low_repayment_indicator(df)
    assert flags.iloc[0] == 0


# ─── Zero Payment ────────────────────────────────────────────────────────────
def test_zero_payment_flag_high():
    df = _make_df(
        pay_amt1=0, pay_amt2=0, pay_amt3=0, pay_amt4=0, pay_amt5=5000, pay_amt6=5000,
        bill_amt1=20000, bill_amt2=20000, bill_amt3=20000, bill_amt4=20000,
    )
    flags = calculate_zero_payment_indicator(df)
    assert flags.iloc[0] == 2


def test_zero_payment_flag_moderate():
    df = _make_df(
        pay_amt1=0, pay_amt2=0, pay_amt3=0, pay_amt4=5000, pay_amt5=5000, pay_amt6=5000,
        bill_amt1=20000, bill_amt2=20000, bill_amt3=20000,
    )
    flags = calculate_zero_payment_indicator(df)
    assert flags.iloc[0] == 1


# ─── Bill Spike ──────────────────────────────────────────────────────────────
def test_bill_spike_detected():
    df = _make_df(bill_amt1=100000, bill_amt2=20000)
    flags = calculate_bill_spike_indicator(df)
    assert flags.iloc[0] == 2


def test_bill_spike_not_detected():
    df = _make_df()
    flags = calculate_bill_spike_indicator(df)
    assert flags.iloc[0] == 0


# ─── Large Exposure ──────────────────────────────────────────────────────────
def test_large_exposure_flag():
    # Build a portfolio where one customer has a very high limit
    rows = [_base_row(id=i, limit_bal=50000) for i in range(20)]
    rows.append(_base_row(id=21, limit_bal=500000))
    df = _make_df(rows=rows)
    df.loc[df["id"] == 21, "credit_utilisation_ratio"] = 0.85
    flags = calculate_large_exposure_indicator(df)
    assert flags[df["id"] == 21].iloc[0] == 2


# ─── Inconsistent Payment ───────────────────────────────────────────────────
def test_inconsistent_payment_flag():
    # Use values with very high coefficient of variation (std/mean >> 1.5)
    # [100000, 1, 1, 1, 1, 1] => mean ~16667, std ~40824, CV ~2.45
    df = _make_df(pay_amt1=100000, pay_amt2=1, pay_amt3=1, pay_amt4=1, pay_amt5=1, pay_amt6=1)
    flags = calculate_inconsistent_payment_indicator(df)
    assert flags.iloc[0] == 2


def test_consistent_payment_no_flag():
    df = _make_df()
    flags = calculate_inconsistent_payment_indicator(df)
    assert flags.iloc[0] == 0


# ─── Outlier ─────────────────────────────────────────────────────────────────
def test_outlier_detection():
    # Create varied base data so IQR is non-zero, then add an extreme outlier
    rows = []
    for i in range(50):
        rows.append(_base_row(
            id=i,
            limit_bal=50000 + i * 1000,
            bill_amt1=10000 + i * 500, bill_amt2=10000 + i * 500,
            bill_amt3=10000 + i * 500, bill_amt4=10000 + i * 500,
            bill_amt5=10000 + i * 500, bill_amt6=10000 + i * 500,
            pay_amt1=2000 + i * 100, pay_amt2=2000 + i * 100,
            pay_amt3=2000 + i * 100, pay_amt4=2000 + i * 100,
            pay_amt5=2000 + i * 100, pay_amt6=2000 + i * 100,
        ))
    # Extreme outlier across multiple dimensions
    rows.append(_base_row(id=99, limit_bal=99999999,
                          bill_amt1=99999999, bill_amt2=99999999,
                          bill_amt3=99999999, bill_amt4=99999999,
                          bill_amt5=99999999, bill_amt6=99999999,
                          pay_amt1=0, pay_amt2=0, pay_amt3=0,
                          pay_amt4=0, pay_amt5=0, pay_amt6=0))
    df = _make_df(rows=rows)
    flags = calculate_outlier_indicator(df)
    assert flags[df["id"] == 99].iloc[0] == 2


# ─── Score & Level ───────────────────────────────────────────────────────────
def test_fraud_risk_score():
    df = _make_df()
    df["high_utilisation_flag"] = 2
    df["repeated_delay_flag"] = 2
    df["long_delay_flag"] = 0
    df["low_repayment_flag"] = 0
    df["zero_payment_flag"] = 0
    df["bill_spike_flag"] = 0
    df["large_exposure_flag"] = 0
    df["inconsistent_payment_flag"] = 0
    df["outlier_flag"] = 0
    score = calculate_fraud_risk_score(df)
    # high_utilisation (2pts) + repeated_delay (2pts) = 4
    assert score.iloc[0] == 4


def test_risk_level_assignment():
    scores = pd.Series([0, 1, 2, 3, 5, 6, 10])
    levels = assign_fraud_risk_level(scores)
    assert levels.iloc[0] == "Low"
    assert levels.iloc[2] == "Low"
    assert levels.iloc[3] == "Moderate"
    assert levels.iloc[4] == "Moderate"
    assert levels.iloc[5] == "High"
    assert levels.iloc[6] == "High"


# ─── Reason Generation ──────────────────────────────────────────────────────
def test_reason_generation():
    row = pd.Series({
        "high_utilisation_flag": 2,
        "repeated_delay_flag": 0,
        "long_delay_flag": 0,
        "low_repayment_flag": 1,
        "zero_payment_flag": 0,
        "bill_spike_flag": 0,
        "large_exposure_flag": 0,
        "inconsistent_payment_flag": 0,
        "outlier_flag": 0,
    })
    reasons = generate_customer_indicator_reasons(row)
    assert "very high proportion" in reasons
    assert "below typical" in reasons


def test_no_indicator_reason():
    row = pd.Series({
        "high_utilisation_flag": 0,
        "repeated_delay_flag": 0,
        "long_delay_flag": 0,
        "low_repayment_flag": 0,
        "zero_payment_flag": 0,
        "bill_spike_flag": 0,
        "large_exposure_flag": 0,
        "inconsistent_payment_flag": 0,
        "outlier_flag": 0,
    })
    reasons = generate_customer_indicator_reasons(row)
    assert reasons == "No indicators triggered."


# ─── Full Pipeline ───────────────────────────────────────────────────────────
def test_run_fraud_indicators_end_to_end():
    df = _make_df(n=5)
    result = run_fraud_indicators(df)
    assert "fraud_risk_score" in result.columns
    assert "fraud_risk_level" in result.columns
    assert "indicator_count" in result.columns
    assert "indicator_reasons" in result.columns
    assert len(result) == 5


def test_original_df_unchanged():
    df = _make_df(n=3)
    original_cols = list(df.columns)
    _ = run_fraud_indicators(df)
    assert list(df.columns) == original_cols


def test_no_target_required():
    """Fraud indicators must not require default_payment_next_month."""
    df = _make_df(n=3)
    assert "default_payment_next_month" not in df.columns
    result = run_fraud_indicators(df)
    assert "fraud_risk_score" in result.columns


def test_no_division_by_zero():
    """Ensure zero-value edge cases don't crash."""
    df = _make_df(
        limit_bal=0,
        bill_amt1=0, bill_amt2=0, bill_amt3=0,
        bill_amt4=0, bill_amt5=0, bill_amt6=0,
        pay_amt1=0, pay_amt2=0, pay_amt3=0,
        pay_amt4=0, pay_amt5=0, pay_amt6=0,
    )
    result = run_fraud_indicators(df)
    assert not result["fraud_risk_score"].isna().any()


def test_indicator_summary():
    df = _make_df(n=10)
    result = run_fraud_indicators(df)
    summary = generate_indicator_summary(result)
    assert summary["total"] == 10
    assert summary["high"] + summary["moderate"] + summary["low"] == 10


# ─── 8. New Feature Tests (Missing Columns, Partial Exec, Target-less, Custom Rules) ───

def test_missing_column_graceful_handling():
    # Create a DataFrame missing all 'pay_amt' columns (Low Repayment, Zero Payment, Inconsistent Payment should fail to run)
    df = _make_df()
    pay_amt_cols = ["pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6"]
    df = df.drop(columns=pay_amt_cols)
    
    validation = validate_indicator_columns(df)
    assert validation["can_run"] is True
    assert "Low Repayment Ratio" in validation["unavailable_indicators"]
    assert "Zero-Payment Pattern" in validation["unavailable_indicators"]
    assert "Inconsistent Repayment Behaviour" in validation["unavailable_indicators"]
    assert "High Credit Utilisation" in validation["available_indicators"]

    result = run_fraud_indicators(df)
    assert pd.isna(result["low_repayment_flag"].iloc[0])
    assert pd.isna(result["zero_payment_flag"].iloc[0])
    assert pd.isna(result["inconsistent_payment_flag"].iloc[0])
    assert not pd.isna(result["high_utilisation_flag"].iloc[0])


def test_prediction_only_dataset_without_target():
    df = _make_df()
    if "default_payment_next_month" in df.columns:
        df = df.drop(columns=["default_payment_next_month"])
    
    result = run_fraud_indicators(df)
    assert "fraud_risk_score" in result.columns
    assert result["fraud_risk_score"].iloc[0] is not None


def test_threshold_adjustment_behavior():
    import copy
    custom_rules = copy.deepcopy(FRAUD_RULES)
    custom_rules["high_utilisation"]["points"] = 10
    df = _make_df(credit_utilisation_ratio=0.99)
    df["credit_utilisation_ratio"] = 0.99
    
    default_result = run_fraud_indicators(df)
    custom_result = run_fraud_indicators(df, custom_rules)
    
    assert custom_result["fraud_risk_score"].iloc[0] == default_result["fraud_risk_score"].iloc[0] + 8

