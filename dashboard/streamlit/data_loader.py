import os
import json
import joblib
import pandas as pd
import streamlit as st
from dashboard.streamlit.app_config import PATHS

@st.cache_data
def load_csv_data(filepath):
    """Loads a CSV file into a pandas DataFrame."""
    if not os.path.exists(filepath):
        return None
    return pd.read_csv(filepath)

@st.cache_data
def load_cleaned_data(filepath):
    """Loads the main cleaned dataset."""
    return load_csv_data(filepath)

@st.cache_data
def load_model_reports(paths_dict):
    """Loads model performance CSV reports."""
    model_comp = load_csv_data(paths_dict['model_comparison'])
    thresh_df = load_csv_data(paths_dict['threshold_analysis'])
    feat_df = load_csv_data(paths_dict['feature_importance'])
    return model_comp, thresh_df, feat_df

@st.cache_resource
def load_model_pipeline(pipeline_path, metadata_path):
    """Loads the trained machine learning pipeline and metadata."""
    if not os.path.exists(pipeline_path) or not os.path.exists(metadata_path):
        return None, None
        
    pipeline = joblib.load(pipeline_path)
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
        
    return pipeline, metadata
