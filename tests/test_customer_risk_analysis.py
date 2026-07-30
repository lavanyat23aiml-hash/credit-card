import pytest
import pandas as pd
import numpy as np
from dashboard.streamlit.customer_risk_analysis import (
    calculate_component_scores,
    calculate_customer_risk_score,
    determine_customer_risk_level,
    generate_risk_reasons,
    generate_customer_risk_profile,
    DEFAULT_RISK_THRESHOLDS,
    DEFAULT_RISK_WEIGHTS
)

@pytest.fixture
def sample_dataset():
    """Returns a realistic partial dataset with a mix of available and missing columns."""
    return pd.DataFrame([
        {
            "customer_id": "C001",
            "default_probability": 0.85,
            "fraud_risk_score": 12,
            "credit_utilisation_ratio": 0.95,
            "delayed_payment_count": 5,
            "payment_to_bill_ratio": 0.05
        },
        {
            "customer_id": "C002",
            "default_probability": 0.10,
            "fraud_risk_score": 0,
            "credit_utilisation_ratio": 0.20,
            "delayed_payment_count": 0,
            "payment_to_bill_ratio": 1.0
        },
        {
            "customer_id": "C003", # Missing ML and Fraud
            "credit_utilisation_ratio": 0.80,
            "delayed_payment_count": 2,
            "payment_to_bill_ratio": 0.40
        }
    ])

def test_calculate_component_scores(sample_dataset):
    row_high = sample_dataset.iloc[0]
    scores = calculate_component_scores(row_high)
    
    assert scores['ml_risk'] == 85.0
    assert scores['fraud_risk'] == 100.0  # 12 * 10 = 120 -> capped at 100
    assert scores['utilization'] == 95.0
    assert scores['delay'] == pytest.approx(83.33, 0.1)  # 5/6 * 100
    assert scores['repayment'] == pytest.approx(95.0, 0.1) # (1 - 0.05) * 100
    
    row_missing = sample_dataset.iloc[2]
    scores_missing = calculate_component_scores(row_missing)
    assert 'ml_risk' not in scores_missing
    assert 'fraud_risk' not in scores_missing
    assert scores_missing['utilization'] == 80.0

def test_calculate_customer_risk_score(sample_dataset):
    scores_df = calculate_customer_risk_score(sample_dataset)
    
    assert len(scores_df) == 3
    
    # Check C001 (High Risk)
    c1 = scores_df.iloc[0]
    assert c1['overall_risk_score'] > 85.0
    assert c1['confidence_level'] == 'High'
    assert 'ml_risk' in c1['components_used']
    assert len(c1['components_missing']) == 0
    
    # Check C003 (Missing components, weight redistribution)
    c3 = scores_df.iloc[2]
    assert c3['confidence_level'] == 'Medium'
    assert 'ml_risk' in c3['components_missing']
    assert 'fraud_risk' in c3['components_missing']
    assert 'utilization' in c3['components_used']
    
    # For C003, only utilization, delay, and repayment are used.
    # Base weights: util (20), delay (10), repay (10) -> Total = 40
    # Effective weights: util (50%), delay (25%), repay (25%)
    # Utilization score: 80 * 0.5 = 40
    # Delay score: (2/6)*100 = 33.33 * 0.25 = 8.33
    # Repayment score: (1 - 0.4)*100 = 60 * 0.25 = 15.0
    # Expected total ~ 63.33
    assert c3['overall_risk_score'] == pytest.approx(63.33, 0.1)
    
def test_determine_customer_risk_level():
    assert determine_customer_risk_level(15) == "Low"
    assert determine_customer_risk_level(45) == "Moderate"
    assert determine_customer_risk_level(85) == "High"
    
def test_generate_risk_reasons(sample_dataset):
    reasons_high = generate_risk_reasons(sample_dataset.iloc[0])
    assert "High predicted default probability" in reasons_high
    assert "High fraud-risk score" in reasons_high
    assert "High credit utilisation" in reasons_high
    assert "Multiple delayed payments" in reasons_high
    assert "Low repayment ratio" in reasons_high
    
    reasons_low = generate_risk_reasons(sample_dataset.iloc[1])
    assert len(reasons_low) == 0

def test_generate_customer_risk_profile(sample_dataset):
    profile = generate_customer_risk_profile(sample_dataset)
    
    # Check columns
    expected_cols = [
        'customer_id', 'overall_risk_score', 'risk_level', 'confidence_level',
        'risk_reasons', 'components_used', 'components_missing', 'analysis_timestamp',
        'contribution_ml_risk', 'contribution_fraud_risk', 'contribution_utilization',
        'contribution_delay', 'contribution_repayment'
    ]
    for col in expected_cols:
        assert col in profile.columns
        
    assert profile.iloc[0]['risk_level'] == 'High'
    assert profile.iloc[1]['risk_level'] == 'Low'
    assert profile.iloc[2]['risk_level'] == 'Moderate'

def test_empty_dataset_handling():
    empty_df = pd.DataFrame()
    profile = generate_customer_risk_profile(empty_df)
    assert len(profile) == 0
    assert 'overall_risk_score' in profile.columns

def test_no_components_crash():
    df = pd.DataFrame([{"customer_id": "C001", "unrelated_col": 123}])
    profile = generate_customer_risk_profile(df)
    
    assert len(profile) == 1
    assert profile.iloc[0]['overall_risk_score'] == 0
    assert profile.iloc[0]['confidence_level'] == 'Low'
    assert len(profile.iloc[0]['components_missing']) == 5
