import os
import pytest

def test_app_imports_and_structure():
    """Test that app.py and components import without raising critical exceptions."""
    import app
    from dashboard.streamlit import app_config, charts, components, data_loader

def test_model_files_exist():
    """Ensure the machine learning pipeline and metadata exist."""
    assert os.path.exists("models/creditguard_final_pipeline.joblib")
    assert os.path.exists("models/creditguard_model_metadata.json")

def test_csv_files_exist():
    """Ensure the cleaned data and reports exist for the analytics pages."""
    assert os.path.exists("data/processed/creditguard_cleaned.csv")
    assert os.path.exists("reports/model/model_comparison.csv")
    assert os.path.exists("reports/model/threshold_analysis.csv")
    assert os.path.exists("reports/model/feature_importance.csv")

def test_prediction_helper_valid_output():
    """Ensure src.utils.predict_default_risk returns the correct structure for a valid row."""
    import src.utils as utils
    
    dummy_input = {
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
        "credit_utilisation_ratio": 0.2
    }
    
    result = utils.predict_default_risk(dummy_input)
    
    assert "predicted_class" in result
    assert "default_probability" in result
    assert "risk_category" in result
    assert "threshold_used" in result
    
    assert 0.0 <= result["default_probability"] <= 1.0
    assert result["predicted_class"] in [0, 1]
    assert result["risk_category"] in ["Low Risk", "Moderate Risk", "High Risk"]
