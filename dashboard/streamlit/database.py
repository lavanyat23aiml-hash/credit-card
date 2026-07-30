import os
import shutil
import sqlite3
import pandas as pd
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError

from dashboard.streamlit.app_config import PATHS

# -----------------------------------------------------------------------------
# Engine and Session Setup
# -----------------------------------------------------------------------------

# Use absolute or relative path based on PATHS dictionary
# If we assume DB_PATH is in app_config, we'll fetch it or default to data/creditguard.db
DB_PATH = PATHS.get("db_path", "data/creditguard.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# We use check_same_thread=False for Streamlit's threading model with SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -----------------------------------------------------------------------------
# ORM Models
# -----------------------------------------------------------------------------

class UploadHistory(Base):
    __tablename__ = "upload_history"
    
    upload_id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    validation_status = Column(String, index=True)
    quality_score = Column(Float)
    total_rows = Column(Integer)
    total_columns = Column(Integer)
    dataset_version = Column(Integer, index=True)
    is_active = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

class Customer(Base):
    __tablename__ = "customers"
    
    customer_pk = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("upload_history.upload_id"), index=True)
    customer_id = Column(String, index=True)
    financial_attributes = Column(JSON)  # Stores all other columns as JSON

class RiskAnalysis(Base):
    __tablename__ = "risk_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("upload_history.upload_id"), index=True)
    customer_id = Column(String, index=True)
    overall_risk_score = Column(Float)
    risk_level = Column(String, index=True)
    confidence = Column(String)
    component_scores = Column(JSON)
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)

class FraudIndicator(Base):
    __tablename__ = "fraud_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("upload_history.upload_id"), index=True)
    customer_id = Column(String, index=True)
    fraud_score = Column(Float)
    fraud_level = Column(String, index=True)
    triggered_indicators = Column(JSON)
    indicator_count = Column(Integer)

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    username = Column(String)
    role = Column(String)
    action = Column(String, index=True)
    object_type = Column(String)
    object_id = Column(String)
    result = Column(String)
    details = Column(Text)

# -----------------------------------------------------------------------------
# Database Management Methods
# -----------------------------------------------------------------------------

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def get_engine():
    """Return the SQLAlchemy engine."""
    return engine

def get_session():
    """Return a new SQLAlchemy session."""
    return SessionLocal()

# -----------------------------------------------------------------------------
# Audit Logging
# -----------------------------------------------------------------------------

def log_audit_event(username: str, role: str, action: str, object_type: str = None, object_id: str = None, result: str = "SUCCESS", details: str = None):
    """Logs an event to the audit_log table."""
    try:
        with get_session() as db:
            log = AuditLog(
                username=username,
                role=role,
                action=action,
                object_type=object_type,
                object_id=object_id,
                result=result,
                details=details
            )
            db.add(log)
            db.commit()
    except Exception as e:
        # Failsafe: never crash the app due to an audit log failure
        print(f"Audit log failed: {e}")

# -----------------------------------------------------------------------------
# Backup & Restore
# -----------------------------------------------------------------------------

def export_database(target_path: str) -> bool:
    """Exports a copy of the SQLite database."""
    try:
        base_dir = os.path.abspath(PATHS.get("backup_dir", "data/backups"))
        os.makedirs(base_dir, exist_ok=True)
        safe_path = os.path.abspath(target_path)
        
        if not safe_path.startswith(base_dir):
            safe_path = os.path.join(base_dir, os.path.basename(target_path))
            
        shutil.copy2(DB_PATH, safe_path)
        return True
    except Exception as e:
        print(f"Export failed: {str(e.__class__.__name__)}")
        return False

def import_database(source_path: str) -> bool:
    """Imports and overwrites the SQLite database after verifying integrity."""
    try:
        # Verify it's a valid sqlite database
        conn = sqlite3.connect(source_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        res = cursor.fetchone()
        conn.close()
        
        if res and res[0] == "ok":
            shutil.copy2(source_path, DB_PATH)
            return True
        return False
    except Exception:
        return False

# -----------------------------------------------------------------------------
# CRUD & Dataset Operations
# -----------------------------------------------------------------------------

def get_upload_history(include_deleted: bool = False):
    """Retrieves all upload history."""
    try:
        query = "SELECT * FROM upload_history"
        if not include_deleted:
            query += " WHERE is_deleted = 0"
        query += " ORDER BY uploaded_at DESC"
        
        with get_engine().connect() as conn:
            df = pd.read_sql(text(query), conn)
        return df
    except SQLAlchemyError as e:
        print(f"Database error in get_upload_history: {e.__class__.__name__}")
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def save_dataset_to_db(
    customer_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    fraud_df: pd.DataFrame,
    filename: str,
    username: str,
    validation_status: str,
    quality_score: float
) -> int:
    """
    Saves a dataset with customers, risk, and fraud results in a single transaction.
    """
    db = get_session()
    try:
        # 1. Determine version
        latest_version = db.query(UploadHistory).count() + 1
        
        # 2. Insert UploadHistory
        upload = UploadHistory(
            filename=filename,
            uploaded_by=username,
            validation_status=validation_status,
            quality_score=quality_score,
            total_rows=len(customer_df),
            total_columns=len(customer_df.columns),
            dataset_version=latest_version,
            is_active=True # Make new upload active by default
        )
        
        # Deactivate previous active uploads
        db.query(UploadHistory).filter(UploadHistory.is_active == True).update({"is_active": False})
        
        db.add(upload)
        db.flush() # Get upload_id
        upload_id = upload.upload_id
        
        # 3. Insert Customers
        # To handle dynamic columns, we pack non-ID columns into JSON
        cust_records = []
        # Fallback if customer_id doesn't exist (should be validated, but safety first)
        id_col = "customer_id" if "customer_id" in customer_df.columns else "ID"
        
        for _, row in customer_df.iterrows():
            row_dict = row.to_dict()
            c_id = str(row_dict.pop(id_col, "UNKNOWN"))
            cust_records.append(Customer(
                upload_id=upload_id,
                customer_id=c_id,
                financial_attributes=row_dict
            ))
        db.bulk_save_objects(cust_records)
        
        # 4. Insert RiskAnalysis
        if not risk_df.empty:
            risk_records = []
            for _, row in risk_df.iterrows():
                row_dict = row.to_dict()
                c_id = str(row_dict.get(id_col, "UNKNOWN"))
                
                # Extract component scores starting with 'contribution_'
                comps = {k: v for k, v in row_dict.items() if str(k).startswith("contribution_")}
                
                risk_records.append(RiskAnalysis(
                    upload_id=upload_id,
                    customer_id=c_id,
                    overall_risk_score=row_dict.get('overall_risk_score', 0.0),
                    risk_level=row_dict.get('risk_level', 'Unknown'),
                    confidence=row_dict.get('confidence_level', 'Unknown'),
                    component_scores=comps
                ))
            db.bulk_save_objects(risk_records)
            
        # 5. Insert FraudIndicator
        if not fraud_df.empty:
            fraud_records = []
            for _, row in fraud_df.iterrows():
                row_dict = row.to_dict()
                c_id = str(row_dict.get(id_col, "UNKNOWN"))
                
                # Collect indicators
                indicators = []
                for k, v in row_dict.items():
                    if str(k).endswith("_flag") and pd.notna(v) and float(v) > 0:
                        indicators.append(k)
                        
                fraud_records.append(FraudIndicator(
                    upload_id=upload_id,
                    customer_id=c_id,
                    fraud_score=row_dict.get('fraud_risk_score', 0.0),
                    fraud_level=row_dict.get('fraud_risk_level', 'Unknown'),
                    triggered_indicators=indicators,
                    indicator_count=len(indicators)
                ))
            db.bulk_save_objects(fraud_records)

        # Commit Transaction
        db.commit()
        return upload_id
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error in save_dataset: {e.__class__.__name__}")
        raise ValueError("A database error occurred while saving the dataset.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def load_dataset_from_db(upload_id: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads customers, risk analysis, and fraud indicators for a given upload_id.
    Returns (customer_df, risk_df, fraud_df).
    Reconstructs the original customer DataFrame from JSON.
    """
    db = get_session()
    try:
        # Load customers
        customers = db.query(Customer).filter(Customer.upload_id == upload_id).all()
        cust_list = []
        for c in customers:
            d = {"customer_id": c.customer_id}
            if c.financial_attributes:
                d.update(c.financial_attributes)
            cust_list.append(d)
        customer_df = pd.DataFrame(cust_list)
        
        # Load Risk
        risk_list = []
        risks = db.query(RiskAnalysis).filter(RiskAnalysis.upload_id == upload_id).all()
        for r in risks:
            d = {
                "customer_id": r.customer_id,
                "overall_risk_score": r.overall_risk_score,
                "risk_level": r.risk_level,
                "confidence_level": r.confidence
            }
            if r.component_scores:
                d.update(r.component_scores)
            risk_list.append(d)
        risk_df = pd.DataFrame(risk_list)
        
        # Load Fraud
        fraud_list = []
        frauds = db.query(FraudIndicator).filter(FraudIndicator.upload_id == upload_id).all()
        for f in frauds:
            d = {
                "customer_id": f.customer_id,
                "fraud_risk_score": f.fraud_score,
                "fraud_risk_level": f.fraud_level
            }
            if f.triggered_indicators:
                for ind in f.triggered_indicators:
                    d[ind] = 1.0 # Approximate flag value
            fraud_list.append(d)
        fraud_df = pd.DataFrame(fraud_list)
        
        return customer_df, risk_df, fraud_df
    except SQLAlchemyError as e:
        print(f"Database error in load_dataset: {e.__class__.__name__}")
        raise ValueError("A database error occurred while loading the dataset.")
    except Exception as e:
        raise e
    finally:
        db.close()

def delete_dataset(upload_id: int):
    """Soft deletes a dataset."""
    db = get_session()
    try:
        upload = db.query(UploadHistory).filter(UploadHistory.upload_id == upload_id).first()
        if upload:
            upload.is_deleted = True
            if upload.is_active:
                upload.is_active = False
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error in delete_dataset: {e.__class__.__name__}")
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def restore_dataset(upload_id: int):
    """Restores a soft-deleted dataset."""
    db = get_session()
    try:
        upload = db.query(UploadHistory).filter(UploadHistory.upload_id == upload_id).first()
        if upload:
            upload.is_deleted = False
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error in restore_dataset: {e.__class__.__name__}")
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def activate_dataset(upload_id: int):
    """Sets a dataset as active and deactivates others."""
    db = get_session()
    try:
        db.query(UploadHistory).filter(UploadHistory.is_active == True).update({"is_active": False})
        upload = db.query(UploadHistory).filter(UploadHistory.upload_id == upload_id).first()
        if upload and not upload.is_deleted:
            upload.is_active = True
            db.commit()
            return True
        db.rollback()
        return False
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error in activate_dataset: {e.__class__.__name__}")
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def search_customers(customer_id: str = None, risk_level: str = None, fraud_level: str = None, upload_id: int = None):
    """Searches for customers across the joined tables."""
    db = get_session()
    try:
        query = db.query(
            Customer.customer_id,
            RiskAnalysis.overall_risk_score,
            RiskAnalysis.risk_level,
            RiskAnalysis.confidence,
            FraudIndicator.fraud_score,
            FraudIndicator.fraud_level,
            UploadHistory.dataset_version
        ).outerjoin(
            RiskAnalysis, (Customer.customer_id == RiskAnalysis.customer_id) & (Customer.upload_id == RiskAnalysis.upload_id)
        ).outerjoin(
            FraudIndicator, (Customer.customer_id == FraudIndicator.customer_id) & (Customer.upload_id == FraudIndicator.upload_id)
        ).join(
            UploadHistory, Customer.upload_id == UploadHistory.upload_id
        )
        
        # We only want non-deleted uploads
        query = query.filter(UploadHistory.is_deleted == False)

        if upload_id:
            query = query.filter(Customer.upload_id == upload_id)
        if customer_id:
            query = query.filter(Customer.customer_id.like(f"%{customer_id}%"))
        if risk_level and risk_level != "All":
            query = query.filter(RiskAnalysis.risk_level == risk_level)
        if fraud_level and fraud_level != "All":
            query = query.filter(FraudIndicator.fraud_level == fraud_level)
            
        results = query.all()
        
        columns = [
            "Customer ID", "Risk Score", "Risk Level", "Confidence", 
            "Fraud Score", "Fraud Level", "Dataset Version"
        ]
        
        df = pd.DataFrame(results, columns=columns)
        return df
    except SQLAlchemyError as e:
        print(f"Database error in search_customers: {e.__class__.__name__}")
        return pd.DataFrame()
    except Exception as e:
        print(e.__class__.__name__)
        return pd.DataFrame()
    finally:
        db.close()
