import pandas as pd
import numpy as np
import shap
import streamlit as st
import warnings

# Suppress expected SHAP warnings for cleaner logs
warnings.filterwarnings('ignore', category=UserWarning, module='shap')

@st.cache_resource
def get_shap_explainer(_pipeline, _background_data: pd.DataFrame):
    """
    Initializes and returns a SHAP explainer based on the provided pipeline.
    Uses a TreeExplainer for Random Forest / XGBoost models, and a fallback for others.
    Requires _background_data to calculate base values for some explainers.
    Uses streamlit cache to avoid recalculating the explainer overhead.
    """
    if _pipeline is None:
        return None
        
    try:
        # Assuming the pipeline has an estimator as the last step
        model = _pipeline.steps[-1][1] if hasattr(_pipeline, 'steps') else _pipeline
        
        # Check model type to select the right explainer
        model_name = type(model).__name__
        
        if model_name in ['RandomForestClassifier', 'DecisionTreeClassifier', 'GradientBoostingClassifier', 'XGBClassifier', 'LGBMClassifier']:
            # Tree explainer is extremely fast for tree-based models
            explainer = shap.TreeExplainer(model)
        elif model_name in ['LogisticRegression', 'LinearRegression']:
            explainer = shap.LinearExplainer(model, _background_data)
        else:
            # Fallback to KernelExplainer (can be slow, so limit background data)
            explainer = shap.KernelExplainer(model.predict_proba, shap.sample(_background_data, 50))
            
        return explainer
    except Exception as e:
        print(f"Failed to initialize SHAP explainer: {e}")
        return None

def generate_global_feature_importance(df: pd.DataFrame, explainer, feature_names: list, sample_size: int = 500) -> pd.DataFrame:
    """
    Calculates global feature importance across a sample of the dataset.
    Returns a dataframe of features ranked by mean absolute SHAP value.
    """
    if explainer is None or df.empty:
        return pd.DataFrame()
        
    try:
        # Use a sample for global importance to ensure fast UI rendering
        sample_df = df.sample(min(len(df), sample_size), random_state=42)
        X_sample = sample_df.reindex(columns=feature_names, fill_value=0)
        
        shap_values = explainer.shap_values(X_sample)
        
        # Handle 3D array (n_samples, n_features, n_classes) from newer SHAP versions
        if isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
            shap_values = shap_values[:, :, 1]
        # For classifiers, shap_values might be a list where index 1 is the positive class (older SHAP)
        elif isinstance(shap_values, list):
            shap_values = shap_values[1]
            
        # Calculate mean absolute SHAP value for each feature
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': mean_abs_shap
        }).sort_values('Importance', ascending=False).reset_index(drop=True)
        
        return importance_df
    except Exception as e:
        print(f"Failed to generate global feature importance: {e}")
        return pd.DataFrame()

def generate_customer_explanation(customer_row: pd.Series, explainer, feature_names: list) -> dict:
    """
    Generates SHAP values for a single customer and extracts top contributors.
    """
    if explainer is None or customer_row.empty:
        return {}
        
    try:
        # Ensure row is formatted as a 1D dataframe with correct columns
        X_row = pd.DataFrame([customer_row]).reindex(columns=feature_names, fill_value=0)
        
        shap_values = explainer.shap_values(X_row)
        expected_value = explainer.expected_value
        
        # Handle 3D array (n_samples, n_features, n_classes) from newer SHAP versions
        if isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
            shap_values = shap_values[0, :, 1]
            if isinstance(expected_value, (list, np.ndarray)):
                expected_value = expected_value[1]
        # Handle binary classification outputs (older SHAP lists)
        elif isinstance(shap_values, list):
            shap_values = shap_values[1][0]
            expected_value = expected_value[1] if isinstance(expected_value, (list, np.ndarray)) else expected_value
        else:
            shap_values = shap_values[0]
            if isinstance(expected_value, (list, np.ndarray)):
                expected_value = expected_value[0]
        
        # Map values to features
        feature_contributions = []
        for i, feature in enumerate(feature_names):
            feature_contributions.append({
                'Feature': feature,
                'Value': X_row.iloc[0][feature],
                'Contribution': shap_values[i],
                'Direction': 'Increases Risk' if shap_values[i] > 0 else 'Decreases Risk'
            })
            
        # Sort by absolute contribution to find top drivers
        sorted_contributions = sorted(feature_contributions, key=lambda x: abs(x['Contribution']), reverse=True)
        
        # Separate positive and negative contributors
        positive_contributors = [c for c in sorted_contributions if c['Contribution'] > 0]
        negative_contributors = [c for c in sorted_contributions if c['Contribution'] < 0]
        
        # Generate Natural Language Summary
        nl_explanation = generate_natural_language_explanation(
            base_val=expected_value, 
            positive=positive_contributors[:3], 
            negative=negative_contributors[:2]
        )
        
        return {
            'expected_value': expected_value,
            'shap_values': shap_values,
            'contributions': sorted_contributions,
            'top_positive': positive_contributors[:5],
            'top_negative': negative_contributors[:5],
            'nl_explanation': nl_explanation
        }
    except Exception as e:
        print(f"Failed to generate customer explanation: {e}")
        return {}

def generate_natural_language_explanation(base_val: float, positive: list, negative: list) -> str:
    """
    Converts SHAP feature contributions into a human-readable summary.
    """
    explanation = "This customer is predicted to have a credit risk profile driven primarily by the following factors:\n\n"
    
    if positive:
        explanation += "**Factors Increasing Risk:**\n"
        for p in positive:
            val_str = f"{p['Value']:.2f}" if isinstance(p['Value'], float) else str(p['Value'])
            explanation += f"- **{p['Feature'].replace('_', ' ').title()}** (Value: {val_str}): Significantly elevates risk probability.\n"
            
    if negative:
        explanation += "\n**Factors Reducing Risk:**\n"
        for n in negative:
            val_str = f"{n['Value']:.2f}" if isinstance(n['Value'], float) else str(n['Value'])
            explanation += f"- **{n['Feature'].replace('_', ' ').title()}** (Value: {val_str}): Helps to mitigate overall risk.\n"
            
    if not positive and not negative:
        explanation = "No significant distinguishing features were identified for this customer. Their profile closely matches the portfolio average."
        
    return explanation

def generate_prediction_breakdown(customer_row: pd.Series, explainer, feature_names: list) -> pd.DataFrame:
    """
    Returns a tabular breakdown of feature contributions for a specific customer.
    """
    explanation_dict = generate_customer_explanation(customer_row, explainer, feature_names)
    
    if not explanation_dict or 'contributions' not in explanation_dict:
        return pd.DataFrame()
        
    df = pd.DataFrame(explanation_dict['contributions'])
    
    # Format for display
    df['Importance Magnitude'] = df['Contribution'].abs()
    df = df.sort_values('Importance Magnitude', ascending=False).drop(columns=['Importance Magnitude'])
    
    return df
