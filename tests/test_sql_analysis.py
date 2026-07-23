import pytest
import sqlite3
import os
import pandas as pd

DB_PATH = 'data/processed/creditguard.db'

def test_database_and_table_exist():
    assert os.path.exists(DB_PATH), "Database file does not exist"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credit_customers';")
    assert cursor.fetchone() is not None, "Table 'credit_customers' does not exist"
    conn.close()

def test_table_row_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM credit_customers;")
    count = cursor.fetchone()[0]
    assert count == 30000, f"Expected 30000 rows, found {count}"
    conn.close()

def test_target_column():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT default_payment_next_month FROM credit_customers", conn)
    conn.close()
    
    assert not df.empty
    assert set(df['default_payment_next_month'].unique()).issubset({0, 1}), "Target contains invalid values"

def test_views_exist():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    views = ['vw_customer_risk_profile', 'vw_default_summary', 'vw_demographic_risk', 'vw_repayment_risk', 'vw_financial_risk']
    
    for view in views:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='view' AND name='{view}';")
        assert cursor.fetchone() is not None, f"View {view} does not exist"
        
    conn.close()

def test_exported_sql_outputs():
    output_dir = 'data/processed/sql_outputs'
    assert os.path.exists(output_dir)
    
    expected_files = [
        'overall_credit_summary.csv',
        'default_rate_by_sex_sql.csv',
        'default_rate_by_education_sql.csv',
        'default_rate_by_marriage_sql.csv',
        'default_rate_by_age_group_sql.csv',
        'default_rate_by_credit_group_sql.csv',
        'default_rate_by_delay_count_sql.csv',
        'default_rate_by_pay0_sql.csv',
        'financial_metrics_by_default_sql.csv',
        'high_risk_age_credit_segments_sql.csv',
        'high_risk_education_delay_segments_sql.csv',
        'top_defaulter_segments_sql.csv'
    ]
    
    for f in expected_files:
        filepath = os.path.join(output_dir, f)
        assert os.path.exists(filepath), f"File {f} is missing"
        
        df = pd.read_csv(filepath)
        assert not df.empty, f"File {f} is empty"
        assert 'Unnamed: 0' not in df.columns, f"Accidental unnamed index column in {f}"
        
        # Check rates are between 0 and 100 if 'default_rate' is a column
        if 'default_rate' in df.columns:
            assert df['default_rate'].min() >= 0
            assert df['default_rate'].max() <= 100

def test_high_risk_segments():
    filepath = 'data/processed/sql_outputs/top_defaulter_segments_sql.csv'
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        if not df.empty:
            assert df['customer_count'].min() >= 100, "Segment has less than 100 customers"

def test_reports_exist():
    assert os.path.exists('reports/sql/creditguard_sql_analysis_report.md')
    assert os.path.exists('reports/sql/key_sql_insights.txt')
