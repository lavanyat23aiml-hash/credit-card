import pandas as pd
import numpy as np
from datetime import datetime

# Centralized Configurations
DEFAULT_RISK_THRESHOLDS = {
    "low": 0,
    "moderate": 40,
    "high": 70
}

DEFAULT_RISK_WEIGHTS = {
    "ml_risk": 40,
    "fraud_risk": 20,
    "utilization": 20,
    "delay": 10,
    "repayment": 10
}

def calculate_component_scores(row):
    """
    Scales each available risk metric to a 0-100 scale.
    """
    scores = {}
    
    if 'default_probability' in row and not pd.isna(row['default_probability']):
        scores['ml_risk'] = row['default_probability'] * 100
        
    if 'fraud_risk_score' in row and not pd.isna(row['fraud_risk_score']):
        # Assuming a fraud score of 10+ is very high risk (100)
        scores['fraud_risk'] = min(row['fraud_risk_score'] * 10, 100)

    if 'credit_utilisation_ratio' in row and not pd.isna(row['credit_utilisation_ratio']):
        scores['utilization'] = min(max(row['credit_utilisation_ratio'] * 100, 0), 100)
        
    if 'delayed_payment_count' in row and not pd.isna(row['delayed_payment_count']):
        # Assuming 6 delays is maximum (100)
        scores['delay'] = min(row['delayed_payment_count'] / 6.0 * 100, 100)
        
    if 'payment_to_bill_ratio' in row and not pd.isna(row['payment_to_bill_ratio']):
        # Low payment ratio means high risk
        scores['repayment'] = max(0, min((1 - row['payment_to_bill_ratio']) * 100, 100))
        
    return scores

def calculate_customer_risk_score(df: pd.DataFrame, weights: dict = None) -> pd.DataFrame:
    """
    Calculates unified risk score, component contributions, and confidence level.
    Dynamically redistributes weights for missing components.
    """
    w = weights or DEFAULT_RISK_WEIGHTS
    
    if df.empty:
        cols = ['overall_risk_score', 'confidence_level', 'components_used', 'components_missing'] + [f"contribution_{k}" for k in w.keys()]
        return pd.DataFrame(columns=cols, index=df.index)
        
    results = []
    
    for _, row in df.iterrows():
        scores = calculate_component_scores(row)
        available_keys = list(scores.keys())
        
        contributions = {f"contribution_{k}": 0.0 for k in w.keys()}
        total_score = 0.0
        confidence = "Low"
        components_used = []
        components_missing = []
        
        if available_keys:
            total_available_weight = sum(w[k] for k in available_keys)
            
            if total_available_weight > 0:
                for k in w.keys():
                    if k in available_keys:
                        effective_weight = w[k] * (100.0 / total_available_weight)
                        contrib = scores[k] * (effective_weight / 100.0)
                        contributions[f"contribution_{k}"] = round(contrib, 2)
                        total_score += contrib
                        components_used.append(k)
                    else:
                        components_missing.append(k)
            else:
                components_missing = list(w.keys())
        else:
            components_missing = list(w.keys())
                
        # Confidence calculation
        total_components = len(w)
        available_count = len(available_keys)
        
        if available_count == total_components:
            confidence = "High"
        elif available_count >= total_components - 2:
            confidence = "Medium"
        else:
            confidence = "Low"
            
        res = {
            "overall_risk_score": round(total_score, 2),
            "confidence_level": confidence,
            "components_used": components_used,
            "components_missing": components_missing
        }
        res.update(contributions)
        results.append(res)
        
    return pd.DataFrame(results, index=df.index)

def determine_customer_risk_level(score: float, thresholds: dict = None) -> str:
    """Map numeric risk score (0-100) to categorical risk level."""
    t = thresholds or DEFAULT_RISK_THRESHOLDS
    if score >= t["high"]:
        return "High"
    elif score >= t["moderate"]:
        return "Moderate"
    else:
        return "Low"

def generate_risk_reasons(row: pd.Series) -> list:
    """Generate human-readable explanations based on available data metrics."""
    reasons = []
    
    # ML Prediction
    if 'default_probability' in row and pd.notna(row['default_probability']):
        if row['default_probability'] >= 0.5:
            reasons.append("High predicted default probability")
            
    # Fraud Risk
    if 'fraud_risk_score' in row and pd.notna(row['fraud_risk_score']):
        if row['fraud_risk_score'] >= 6:
            reasons.append("High fraud-risk score")
            
    # Financials
    if 'credit_utilisation_ratio' in row and pd.notna(row['credit_utilisation_ratio']):
        if row['credit_utilisation_ratio'] >= 0.8:
            reasons.append("High credit utilisation")
            
    if 'delayed_payment_count' in row and pd.notna(row['delayed_payment_count']):
        if row['delayed_payment_count'] >= 3:
            reasons.append("Multiple delayed payments")
            
    if 'payment_to_bill_ratio' in row and pd.notna(row['payment_to_bill_ratio']):
        if row['payment_to_bill_ratio'] <= 0.2:
            reasons.append("Low repayment ratio")
            
    # Fallback if no specific reasons triggered but score is high
    if not reasons and row.get('overall_risk_score', 0) >= DEFAULT_RISK_THRESHOLDS['moderate']:
        reasons.append("Accumulated moderate risk factors")
        
    return reasons

def generate_customer_risk_profile(df: pd.DataFrame, thresholds: dict = None, weights: dict = None) -> pd.DataFrame:
    """
    Orchestration layer that consumes base DataFrame, calculates unified risk scores,
    and returns a complete structured customer risk profile.
    """
    # 1. Calculate the core score components
    score_df = calculate_customer_risk_score(df, weights)
    
    # 2. Combine with original DF
    combined = pd.concat([df, score_df], axis=1)
    
    # 3. Add Risk Levels and Reasons
    combined['risk_level'] = combined['overall_risk_score'].apply(
        lambda s: determine_customer_risk_level(s, thresholds)
    )
    combined['risk_reasons'] = combined.apply(generate_risk_reasons, axis=1)
    combined['analysis_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 4. Standardise output format
    output_cols = [
        'overall_risk_score',
        'risk_level',
        'confidence_level',
        'risk_reasons',
        'components_used',
        'components_missing',
        'analysis_timestamp'
    ]
    
    # Add optional context columns if they exist
    context_cols = [
        'customer_id',
        'fraud_risk_score',
        'fraud_risk_level',
        'default_probability',
        'predicted_class',
        'credit_utilisation_ratio',
        'payment_to_bill_ratio',
        'delayed_payment_count'
    ]
    for c in context_cols:
        if c in combined.columns:
            output_cols.insert(0, c)
            
    # Add component contributions
    w = weights or DEFAULT_RISK_WEIGHTS
    for k in w.keys():
        contrib_col = f"contribution_{k}"
        if contrib_col in combined.columns:
            output_cols.append(contrib_col)
            
    # Dedup just in case
    output_cols = list(dict.fromkeys(output_cols))
    
    return combined[output_cols].copy()
