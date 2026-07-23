import joblib
import json
import pandas as pd
import os

def load_model_artifacts():
    pipeline_path = 'models/creditguard_final_pipeline.joblib'
    metadata_path = 'models/creditguard_model_metadata.json'
    
    if not os.path.exists(pipeline_path) or not os.path.exists(metadata_path):
        raise FileNotFoundError("Model artifacts not found. Please train the model first.")
        
    pipeline = joblib.load(pipeline_path)
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
        
    return pipeline, metadata

def predict_default_risk(input_data):
    """
    Predicts the default risk for a given customer.
    
    Args:
        input_data (dict or pd.Series or pd.DataFrame): The input features.
        
    Returns:
        dict: A dictionary containing predicted_class, default_probability, risk_category, and threshold_used.
    """
    pipeline, metadata = load_model_artifacts()
    
    if isinstance(input_data, dict):
        df = pd.DataFrame([input_data])
    elif isinstance(input_data, pd.Series):
        df = pd.DataFrame([input_data])
    elif isinstance(input_data, pd.DataFrame):
        df = input_data.copy()
    else:
        raise ValueError("Input data must be a dictionary, pandas Series, or pandas DataFrame.")
        
    expected_features = metadata['feature_names']
    for f in expected_features:
        if f not in df.columns:
            raise ValueError(f"Missing required feature: {f}")
            
    # Ensure correct order
    df = df[expected_features]
    
    probs = pipeline.predict_proba(df)[:, 1]
    prob = float(probs[0])
    
    threshold = metadata['selected_threshold']
    pred_class = int(prob >= threshold)
    
    if prob < (threshold * 0.5):
        risk = "Low Risk"
    elif prob < threshold:
        risk = "Moderate Risk"
    else:
        risk = "High Risk"
        
    return {
        "predicted_class": pred_class,
        "default_probability": round(prob, 4),
        "risk_category": risk,
        "threshold_used": threshold
    }
