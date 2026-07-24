# App Configuration and shared constants
from dashboard.streamlit.styles import PALETTE, CHART_COLORS, FONT_STACK

APP_TITLE = "CreditGuard | Credit Risk Analytics"
APP_SUBTITLE = "Portfolio Analytics and Default Risk Estimation"

# Re-export PALETTE as COLORS for backward compatibility
COLORS = PALETTE

PAGE_HOME        = "1. Executive Overview"
PAGE_SEGMENT     = "2. Customer Segmentation"
PAGE_FINANCE     = "3. Repayment & Financial Behaviour"
PAGE_PERFORMANCE = "4. Model Performance"
PAGE_EXPLORER    = "5. High-Risk Customer Explorer"
PAGE_PREDICT     = "6. Customer Risk Prediction"
PAGE_DOCS        = "7. Project Documentation"

PAGES = [
    PAGE_HOME,
    PAGE_SEGMENT,
    PAGE_FINANCE,
    PAGE_PERFORMANCE,
    PAGE_EXPLORER,
    PAGE_PREDICT,
    PAGE_DOCS,
]

PATHS = {
    "cleaned_data":      "data/processed/creditguard_cleaned.csv",
    "model_comparison":  "reports/model/model_comparison.csv",
    "threshold_analysis":"reports/model/threshold_analysis.csv",
    "feature_importance":"reports/model/feature_importance.csv",
    "model_pipeline":    "models/creditguard_final_pipeline.joblib",
    "model_metadata":    "models/creditguard_model_metadata.json",
    "readme":            "README.md",
}
