import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from dashboard.streamlit.explainable_ai import (
    get_shap_explainer,
    generate_global_feature_importance,
    generate_customer_explanation,
    generate_natural_language_explanation,
    generate_prediction_breakdown
)
import streamlit as st

@pytest.fixture(autouse=True)
def clear_cache():
    st.cache_resource.clear()


@pytest.fixture
def mock_data():
    return pd.DataFrame({
        'credit_utilisation_ratio': [0.1, 0.5, 0.9, 0.2, 0.8],
        'delayed_payment_count': [0, 2, 5, 1, 4],
        'payment_to_bill_ratio': [1.0, 0.8, 0.2, 0.9, 0.5]
    })

@pytest.fixture
def feature_names():
    return ['credit_utilisation_ratio', 'delayed_payment_count', 'payment_to_bill_ratio']

@pytest.fixture
def rf_pipeline(mock_data):
    X = mock_data
    y = np.array([0, 0, 1, 0, 1])
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    return Pipeline([('classifier', model)])

@pytest.fixture
def lr_pipeline(mock_data):
    X = mock_data
    y = np.array([0, 0, 1, 0, 1])
    model = LogisticRegression(random_state=42)
    model.fit(X, y)
    return Pipeline([('classifier', model)])

def test_get_shap_explainer_tree(rf_pipeline, mock_data):
    explainer = get_shap_explainer(rf_pipeline, mock_data)
    assert explainer is not None
    assert type(explainer).__name__ == 'TreeExplainer'

def test_get_shap_explainer_linear(lr_pipeline, mock_data):
    explainer = get_shap_explainer(lr_pipeline, mock_data)
    assert explainer is not None
    assert type(explainer).__name__ == 'LinearExplainer'

def test_get_shap_explainer_none():
    explainer = get_shap_explainer(None, pd.DataFrame())
    assert explainer is None

def test_generate_global_feature_importance(rf_pipeline, mock_data, feature_names):
    explainer = get_shap_explainer(rf_pipeline, mock_data)
    importance_df = generate_global_feature_importance(mock_data, explainer, feature_names)
    assert not importance_df.empty
    assert list(importance_df.columns) == ['Feature', 'Importance']
    assert len(importance_df) == len(feature_names)

def test_generate_global_feature_importance_empty(rf_pipeline, feature_names):
    explainer = get_shap_explainer(rf_pipeline, pd.DataFrame())
    importance_df = generate_global_feature_importance(pd.DataFrame(), explainer, feature_names)
    assert importance_df.empty

def test_generate_customer_explanation(rf_pipeline, mock_data, feature_names):
    explainer = get_shap_explainer(rf_pipeline, mock_data)
    customer_row = mock_data.iloc[2]
    explanation = generate_customer_explanation(customer_row, explainer, feature_names)
    
    assert explanation is not None
    assert 'expected_value' in explanation
    assert 'shap_values' in explanation
    assert 'contributions' in explanation
    assert 'nl_explanation' in explanation
    
    # Check that contributions list is populated
    assert len(explanation['contributions']) == len(feature_names)
    assert explanation['contributions'][0]['Feature'] in feature_names

def test_generate_customer_explanation_missing_features(rf_pipeline, mock_data, feature_names):
    explainer = get_shap_explainer(rf_pipeline, mock_data)
    # Remove a feature to simulate partial dataset
    customer_row = mock_data.iloc[2].drop('delayed_payment_count')
    explanation = generate_customer_explanation(customer_row, explainer, feature_names)
    
    # Should not crash and should fill missing with 0
    assert explanation is not None
    assert 'contributions' in explanation
    
    # Find the missing feature in the contributions to see if it was processed
    missing_contrib = next(c for c in explanation['contributions'] if c['Feature'] == 'delayed_payment_count')
    assert missing_contrib is not None

def test_generate_natural_language_explanation():
    base_val = 0.5
    positive = [{'Feature': 'credit_utilisation', 'Value': 0.9, 'Contribution': 0.1}]
    negative = [{'Feature': 'payment_to_bill_ratio', 'Value': 1.0, 'Contribution': -0.05}]
    
    explanation = generate_natural_language_explanation(base_val, positive, negative)
    
    assert "Factors Increasing Risk" in explanation
    assert "Credit Utilisation" in explanation
    assert "Factors Reducing Risk" in explanation
    assert "Payment To Bill Ratio" in explanation

def test_generate_natural_language_explanation_empty():
    explanation = generate_natural_language_explanation(0.5, [], [])
    assert "No significant distinguishing features" in explanation

def test_generate_prediction_breakdown(rf_pipeline, mock_data, feature_names):
    explainer = get_shap_explainer(rf_pipeline, mock_data)
    customer_row = mock_data.iloc[0]
    breakdown_df = generate_prediction_breakdown(customer_row, explainer, feature_names)
    
    assert not breakdown_df.empty
    assert list(breakdown_df.columns) == ['Feature', 'Value', 'Contribution', 'Direction']
    assert len(breakdown_df) == len(feature_names)
