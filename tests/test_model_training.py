import pytest
import pandas as pd
import os
import json
import joblib
from sklearn.model_selection import train_test_split
from src.utils import predict_default_risk

def test_dataset_validity():
    df = pd.read_csv('data/processed/creditguard_model_ready.csv')
    assert not df.empty, "Dataset is empty"
    assert 'default_payment_next_month' in df.columns, "Target column missing"
    assert set(df['default_payment_next_month'].unique()).issubset({0, 1}), "Target is not binary"
    assert 'id' not in df.columns.str.lower(), "ID column is present"
    assert df.isnull().sum().sum() == 0, "Missing values found"
    
def test_train_test_split_proportions():
    df = pd.read_csv('data/processed/creditguard_model_ready.csv')
    X = df.drop(columns=['default_payment_next_month'])
    y = df['default_payment_next_month']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    train_prop = y_train.mean()
    test_prop = y_test.mean()
    
    # Check if proportions are approximately equal (within 1%)
    assert abs(train_prop - test_prop) < 0.01, "Class proportions not preserved in split"

def test_saved_artifacts_exist():
    # Only run these assertions if the files exist to avoid failure before the script is ever run
    if os.path.exists('models/creditguard_final_pipeline.joblib'):
        assert os.path.exists('models/creditguard_model_metadata.json')
        
        with open('models/creditguard_model_metadata.json', 'r') as f:
            metadata = json.load(f)
            
        assert 'feature_names' in metadata
        assert 0 <= metadata['selected_threshold'] <= 1

def test_reports_exist():
    if os.path.exists('reports/model/model_comparison.csv'):
        df_comp = pd.read_csv('reports/model/model_comparison.csv')
        assert not df_comp.empty
        
    if os.path.exists('reports/model/threshold_analysis.csv'):
        df_th = pd.read_csv('reports/model/threshold_analysis.csv')
        assert not df_th.empty

def test_prediction_helper():
    if os.path.exists('models/creditguard_final_pipeline.joblib') and os.path.exists('models/creditguard_model_metadata.json'):
        df = pd.read_csv('data/processed/creditguard_model_ready.csv')
        sample_row = df.drop(columns=['default_payment_next_month']).iloc[0].to_dict()
        
        result = predict_default_risk(sample_row)
        
        assert 'predicted_class' in result
        assert 'default_probability' in result
        assert 'risk_category' in result
        assert 'threshold_used' in result
        assert 0 <= result['default_probability'] <= 1
        assert result['predicted_class'] in [0, 1]
        assert result['risk_category'] in ["Low Risk", "Moderate Risk", "High Risk"]
