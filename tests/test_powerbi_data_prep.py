import os
import pandas as pd
import pytest

OUTPUT_DIR = "data/processed/powerbi/"

def test_fact_table_properties():
    """Verify FactCreditCustomer has exactly 30,000 rows and correct columns."""
    fact_path = os.path.join(OUTPUT_DIR, "FactCreditCustomer.csv")
    assert os.path.exists(fact_path), "Fact table missing."
    
    df = pd.read_csv(fact_path)
    assert len(df) == 30000, "Fact table must have exactly 30,000 rows."
    assert "Unnamed: 0" not in df.columns, "Found unnamed index column."
    assert df['id'].nunique() == 30000, "Customer IDs must be unique."

@pytest.mark.parametrize("dim_file, key_col", [
    ("DimAgeGroup.csv", "age_group"),
    ("DimCreditLimitGroup.csv", "credit_limit_group"),
    ("DimSex.csv", "sex"),
    ("DimEducation.csv", "education"),
    ("DimMarriage.csv", "marriage"),
    ("DimDefaultStatus.csv", "default_payment_next_month")
])
def test_dimension_table_uniqueness(dim_file, key_col):
    """Ensure dimension tables have strictly unique primary keys."""
    dim_path = os.path.join(OUTPUT_DIR, dim_file)
    assert os.path.exists(dim_path), f"Dimension file {dim_file} missing."
    
    df = pd.read_csv(dim_path)
    assert len(df) == df[key_col].nunique(), f"Primary key {key_col} is not unique in {dim_file}."
    assert "Unnamed: 0" not in df.columns, f"Found unnamed index column in {dim_file}."

def test_model_reports_exist():
    """Ensure ML reports were copied over correctly."""
    for f in ["ModelPerformance.csv", "ThresholdAnalysis.csv", "FeatureImportance.csv"]:
        path = os.path.join(OUTPUT_DIR, f)
        assert os.path.exists(path), f"Model report {f} missing."
        
        # Test it's not totally empty (assuming Phase 6 completed)
        df = pd.read_csv(path)
        assert len(df.columns) > 0, f"Table {f} has no columns."
