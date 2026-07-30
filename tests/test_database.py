import pytest
import os
import sqlite3
import pandas as pd
from sqlalchemy import text
from dashboard.streamlit.database import (
    get_engine, init_db, save_dataset_to_db, load_dataset_from_db,
    get_upload_history, delete_dataset, restore_dataset, activate_dataset,
    search_customers, log_audit_event, export_database, import_database
)
from dashboard.streamlit.app_config import PATHS

@pytest.fixture(autouse=True)
def setup_test_db(tmpdir, monkeypatch):
    """Sets up a temporary database for testing."""
    db_path = str(tmpdir.join("test_creditguard.db"))
    monkeypatch.setitem(PATHS, "db_path", db_path)
    
    # Re-initialize engine to point to test db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import dashboard.streamlit.database as db_module
    
    test_engine = create_engine(f"sqlite:///{db_path}")
    db_module.engine = test_engine
    db_module.SessionLocal = sessionmaker(bind=test_engine)
    db_module.DB_PATH = db_path
    
    # Create tables
    init_db()
    
    yield db_path
    
    # Teardown
    test_engine.dispose()
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def sample_data():
    customer_df = pd.DataFrame([
        {"customer_id": "C001", "limit_balance": 50000, "age": 30},
        {"customer_id": "C002", "limit_balance": 100000, "age": 45}
    ])
    
    risk_df = pd.DataFrame([
        {"customer_id": "C001", "overall_risk_score": 85.0, "risk_level": "High", "confidence_level": "High", "contribution_ml": 40},
        {"customer_id": "C002", "overall_risk_score": 25.0, "risk_level": "Low", "confidence_level": "High"}
    ])
    
    fraud_df = pd.DataFrame([
        {"customer_id": "C001", "fraud_risk_score": 8.0, "fraud_risk_level": "High", "high_utilisation_flag": 2},
        {"customer_id": "C002", "fraud_risk_score": 1.0, "fraud_risk_level": "Low"}
    ])
    
    return customer_df, risk_df, fraud_df

def test_database_initialization(setup_test_db):
    """Test if tables are created successfully."""
    engine = get_engine()
    with engine.connect() as conn:
        tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        table_names = [t[0] for t in tables]
        assert "upload_history" in table_names
        assert "customers" in table_names
        assert "risk_analysis" in table_names
        assert "fraud_indicators" in table_names
        assert "audit_log" in table_names

def test_save_and_load_dataset(sample_data):
    customer_df, risk_df, fraud_df = sample_data
    
    upload_id = save_dataset_to_db(
        customer_df, risk_df, fraud_df,
        filename="test_upload.csv",
        username="admin",
        validation_status="pass",
        quality_score=95.0
    )
    
    assert upload_id == 1
    
    # Load it back
    l_cust, l_risk, l_fraud = load_dataset_from_db(upload_id)
    
    assert len(l_cust) == 2
    assert "limit_balance" in l_cust.columns
    assert l_cust[l_cust["customer_id"] == "C001"]["limit_balance"].iloc[0] == 50000
    
    assert len(l_risk) == 2
    assert l_risk[l_risk["customer_id"] == "C001"]["risk_level"].iloc[0] == "High"
    
    assert len(l_fraud) == 2
    assert l_fraud[l_fraud["customer_id"] == "C001"]["fraud_risk_score"].iloc[0] == 8.0

def test_dataset_versioning_and_soft_delete(sample_data):
    customer_df, risk_df, fraud_df = sample_data
    
    # Save v1
    upload_1 = save_dataset_to_db(customer_df, risk_df, fraud_df, "v1.csv", "admin", "pass", 100)
    # Save v2
    upload_2 = save_dataset_to_db(customer_df, risk_df, fraud_df, "v2.csv", "admin", "pass", 100)
    
    history = get_upload_history(include_deleted=False)
    assert len(history) == 2
    
    # v2 should be active, v1 inactive
    assert history[history['upload_id'] == upload_2]['is_active'].iloc[0] == True
    assert history[history['upload_id'] == upload_1]['is_active'].iloc[0] == False
    
    # Soft delete v1
    assert delete_dataset(upload_1) == True
    
    # Check history without deleted
    history_no_del = get_upload_history(include_deleted=False)
    assert len(history_no_del) == 1
    assert history_no_del['upload_id'].iloc[0] == upload_2
    
    # Check history with deleted
    history_with_del = get_upload_history(include_deleted=True)
    assert len(history_with_del) == 2
    
    # Restore v1
    assert restore_dataset(upload_1) == True
    assert len(get_upload_history(include_deleted=False)) == 2
    
    # Activate v1
    assert activate_dataset(upload_1) == True
    history_after = get_upload_history(include_deleted=False)
    assert history_after[history_after['upload_id'] == upload_1]['is_active'].iloc[0] == True
    assert history_after[history_after['upload_id'] == upload_2]['is_active'].iloc[0] == False

def test_search_customers(sample_data):
    customer_df, risk_df, fraud_df = sample_data
    save_dataset_to_db(customer_df, risk_df, fraud_df, "test.csv", "admin", "pass", 100)
    
    # Search by ID
    res1 = search_customers(customer_id="001")
    assert len(res1) == 1
    assert res1["Risk Level"].iloc[0] == "High"
    
    # Search by Risk Level
    res2 = search_customers(risk_level="Low")
    assert len(res2) == 1
    assert res2["Customer ID"].iloc[0] == "C002"

def test_audit_logging():
    log_audit_event("test_user", "Admin", "TEST_ACTION", "System", "1", "SUCCESS", "Detail")
    
    with get_engine().connect() as conn:
        logs = pd.read_sql(text("SELECT * FROM audit_log"), conn)
        
    assert len(logs) == 1
    assert logs["username"].iloc[0] == "test_user"
    assert logs["action"].iloc[0] == "TEST_ACTION"

def test_backup_and_restore(setup_test_db, tmpdir):
    log_audit_event("admin", "Admin", "TEST", "None", "0", "SUCCESS")
    
    # Export to a safe data directory
    safe_backup_dir = os.path.abspath(PATHS.get("backup_dir", "data/backups"))
    os.makedirs(safe_backup_dir, exist_ok=True)
    backup_path = os.path.join(safe_backup_dir, "test_backup.db")
    
    assert export_database(backup_path) == True
    assert os.path.exists(backup_path)
    
    # Delete test db (dispose engine first to release file lock on Windows)
    from dashboard.streamlit.database import engine
    engine.dispose()
    try:
        os.remove(setup_test_db)
    except PermissionError:
        pass # If we still can't remove it on Windows, it's fine, import will try to overwrite
    
    # Import
    assert import_database(backup_path) == True
    
    # Verify data is still there
    with get_engine().connect() as conn:
        logs = pd.read_sql(text("SELECT * FROM audit_log"), conn)
        assert len(logs) == 1
        
    # Clean up after all assertions
    if os.path.exists(backup_path):
        os.remove(backup_path)

def test_sql_injection_prevention():
    """SQLAlchemy parameterizes queries, protecting against injection."""
    # Attempting to search with an injected ID
    injected_id = "C001'; DROP TABLE customers; --"
    res = search_customers(customer_id=injected_id)
    assert len(res) == 0
    
    # Ensure customers table still exists
    with get_engine().connect() as conn:
        tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        table_names = [t[0] for t in tables]
        assert "customers" in table_names
