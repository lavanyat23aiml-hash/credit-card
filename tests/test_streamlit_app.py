"""
Tests for the CreditGuard Streamlit application.
Validates imports, file existence, data integrity, calculations, and model output.
"""

import os
import json
import pytest
import pandas as pd


# ─── 1. Module Imports ────────────────────────────────────────────────────────

def test_app_imports():
    """All application modules must import cleanly."""
    import app  # noqa: F401
    from dashboard.streamlit import app_config, styles, charts, components, data_loader  # noqa: F401


def test_page_routes_defined():
    """All 8 page route constants must be defined in app_config."""
    from dashboard.streamlit.app_config import (
        PAGE_HOME, PAGE_UPLOAD, PAGE_SEGMENT, PAGE_FINANCE,
        PAGE_PERFORMANCE, PAGE_EXPLORER, PAGE_PREDICT, PAGE_DOCS, PAGES,
    )
    assert len(PAGES) == 8

    pages = {PAGE_HOME, PAGE_UPLOAD, PAGE_SEGMENT, PAGE_FINANCE,
             PAGE_PERFORMANCE, PAGE_EXPLORER, PAGE_PREDICT, PAGE_DOCS}
    assert len(pages) == 8


# ─── 2. Required Files ────────────────────────────────────────────────────────

def test_model_files_exist():
    assert os.path.exists("models/creditguard_final_pipeline.joblib"), "Pipeline file missing"
    assert os.path.exists("models/creditguard_model_metadata.json"),   "Metadata file missing"


def test_csv_files_exist():
    assert os.path.exists("data/processed/creditguard_cleaned.csv"),   "Cleaned data missing"
    assert os.path.exists("reports/model/model_comparison.csv"),       "Model comparison missing"
    assert os.path.exists("reports/model/threshold_analysis.csv"),     "Threshold analysis missing"
    assert os.path.exists("reports/model/feature_importance.csv"),     "Feature importance missing"


# ─── 3. Data Loading & Calculations ──────────────────────────────────────────

def test_cleaned_data_loads_with_expected_columns():
    df = pd.read_csv("data/processed/creditguard_cleaned.csv")
    required = [
        "id", "limit_bal", "age", "sex", "education", "marriage",
        "default_payment_next_month", "has_payment_delay",
        "credit_utilisation_ratio", "delayed_payment_count", "maximum_delay_months",
        "average_bill_amount", "average_payment_amount", "payment_to_bill_ratio",
        "pay_0",
    ]
    for col in required:
        assert col in df.columns, f"Column '{col}' missing from cleaned data"


def test_default_rate_calculation():
    df = pd.read_csv("data/processed/creditguard_cleaned.csv")
    total = len(df)
    defaults = df["default_payment_next_month"].sum()
    rate = defaults / total
    assert 0.0 < rate < 1.0, f"Unexpected default rate: {rate}"
    assert abs(rate - 0.221) < 0.05, f"Default rate far from expected ~22%: {rate}"


def test_filtered_calculations_return_valid_values():
    df = pd.read_csv("data/processed/creditguard_cleaned.csv")
    # Simulate filtering to one age group
    if "age_group" in df.columns:
        subset = df[df["age_group"] == df["age_group"].value_counts().idxmax()]
        assert len(subset) > 0
        rate = subset["default_payment_next_month"].mean()
        assert 0.0 <= rate <= 1.0


def test_empty_filter_handled():
    """Filtering to an impossible combination returns an empty DataFrame without error."""
    df = pd.read_csv("data/processed/creditguard_cleaned.csv")
    empty = df[(df["age"] < 0)]  # impossible
    assert empty.empty  # Must return empty, not raise


# ─── 4. Segment Logic ─────────────────────────────────────────────────────────

def test_high_risk_segments_min_100():
    df = pd.read_csv("data/processed/creditguard_cleaned.csv")
    if "age_group" not in df.columns or "credit_limit_group" not in df.columns:
        pytest.skip("Required grouping columns not found")

    # Add delay_status if missing
    if "delay_status" not in df.columns:
        df["delay_status"] = df["has_payment_delay"].map({1: "Delayed", 0: "No Delay"})

    grp = df.groupby(["age_group", "credit_limit_group", "education_label", "marriage_label", "delay_status"])
    seg = grp.agg(customer_count=("id", "count")).reset_index()
    filtered = seg[seg["customer_count"] >= 100]
    assert len(filtered) > 0, "No segments with ≥ 100 customers found"
    assert (filtered["customer_count"] >= 100).all(), "Some segments have < 100 customers"


# ─── 5. Explorer / Search ─────────────────────────────────────────────────────

def test_customer_id_search():
    df = pd.read_csv("data/processed/creditguard_cleaned.csv")
    sample_id = str(df["id"].iloc[0])
    result = df[df["id"].astype(str).str.contains(sample_id, na=False)]
    assert not result.empty, "Customer ID search returned no results"


def test_csv_export_data_generated():
    df = pd.read_csv("data/processed/creditguard_cleaned.csv")
    subset = df[df["default_payment_next_month"] == 1].head(50)
    csv_bytes = subset.to_csv(index=False).encode("utf-8")
    assert len(csv_bytes) > 0, "CSV export produced empty bytes"


# ─── 6. Prediction Pipeline ───────────────────────────────────────────────────

def test_prediction_output_structure():
    """predict_default_risk must return correct keys and value ranges."""
    from src.utils import predict_default_risk

    dummy = {
        "limit_bal": 50000, "sex": 2, "education": 2, "marriage": 2, "age": 30,
        "pay_0": 0, "pay_2": 0, "pay_3": 0, "pay_4": 0, "pay_5": 0, "pay_6": 0,
        "bill_amt1": 10000, "bill_amt2": 10000, "bill_amt3": 10000,
        "bill_amt4": 10000, "bill_amt5": 10000, "bill_amt6": 10000,
        "pay_amt1": 1000, "pay_amt2": 1000, "pay_amt3": 1000,
        "pay_amt4": 1000, "pay_amt5": 1000, "pay_amt6": 1000,
        "average_bill_amount": 10000, "total_bill_amount": 60000,
        "average_payment_amount": 1000, "total_payment_amount": 6000,
        "payment_to_bill_ratio": 0.1, "maximum_delay_months": 0,
        "delayed_payment_count": 0, "has_payment_delay": 0,
        "credit_utilisation_ratio": 0.2,
    }
    result = predict_default_risk(dummy)
    assert "predicted_class"     in result
    assert "default_probability" in result
    assert "risk_category"       in result
    assert "threshold_used"      in result
    assert 0.0 <= result["default_probability"] <= 1.0
    assert result["predicted_class"] in [0, 1]
    assert result["risk_category"]   in ["Low Risk", "Moderate Risk", "High Risk"]


def test_probability_between_0_and_1():
    from src.utils import predict_default_risk
    dummy = {
        "limit_bal": 100000, "sex": 1, "education": 1, "marriage": 1, "age": 45,
        "pay_0": 2, "pay_2": 2, "pay_3": 1, "pay_4": 0, "pay_5": 0, "pay_6": 0,
        "bill_amt1": 80000, "bill_amt2": 70000, "bill_amt3": 60000,
        "bill_amt4": 50000, "bill_amt5": 40000, "bill_amt6": 30000,
        "pay_amt1": 0, "pay_amt2": 500, "pay_amt3": 1000,
        "pay_amt4": 1000, "pay_amt5": 1000, "pay_amt6": 1000,
        "average_bill_amount": 55000, "total_bill_amount": 330000,
        "average_payment_amount": 750, "total_payment_amount": 4500,
        "payment_to_bill_ratio": 0.014, "maximum_delay_months": 2,
        "delayed_payment_count": 3, "has_payment_delay": 1,
        "credit_utilisation_ratio": 0.92,
    }
    result = predict_default_risk(dummy)
    assert 0.0 <= result["default_probability"] <= 1.0


def test_threshold_matches_metadata():
    from src.utils import predict_default_risk
    with open("models/creditguard_model_metadata.json", "r") as f:
        metadata = json.load(f)
    saved_threshold = metadata.get("final_threshold", metadata.get("selected_threshold"))
    assert saved_threshold is not None, "No threshold found in metadata"

    dummy = {
        "limit_bal": 50000, "sex": 2, "education": 2, "marriage": 2, "age": 30,
        "pay_0": 0, "pay_2": 0, "pay_3": 0, "pay_4": 0, "pay_5": 0, "pay_6": 0,
        "bill_amt1": 10000, "bill_amt2": 10000, "bill_amt3": 10000,
        "bill_amt4": 10000, "bill_amt5": 10000, "bill_amt6": 10000,
        "pay_amt1": 1000, "pay_amt2": 1000, "pay_amt3": 1000,
        "pay_amt4": 1000, "pay_amt5": 1000, "pay_amt6": 1000,
        "average_bill_amount": 10000, "total_bill_amount": 60000,
        "average_payment_amount": 1000, "total_payment_amount": 6000,
        "payment_to_bill_ratio": 0.1, "maximum_delay_months": 0,
        "delayed_payment_count": 0, "has_payment_delay": 0,
        "credit_utilisation_ratio": 0.2,
    }
    result = predict_default_risk(dummy)
    assert result["threshold_used"] == saved_threshold, (
        f"Threshold mismatch: got {result['threshold_used']}, expected {saved_threshold}"
    )


# ─── 7. Style Module ──────────────────────────────────────────────────────────

def test_styles_module_exports():
    """styles.py must export all required rendering functions."""
    from dashboard.streamlit import styles
    required_fns = [
        "inject_global_styles", "render_page_header", "section_start", "section_end",
        "render_kpi_card", "render_info_panel", "render_risk_result_card",
        "render_sidebar_brand", "render_sidebar_footer",
    ]
    for fn in required_fns:
        assert hasattr(styles, fn), f"styles.py missing function: {fn}"
