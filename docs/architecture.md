# CreditGuard — System Architecture

## Overview

CreditGuard is a layered, modular application. Each layer has a single responsibility and communicates with adjacent layers through well-defined interfaces.

---

## Architecture Diagram

```
╔════════════════════════════════════════════════════════════════╗
║                     PRESENTATION LAYER                         ║
║                       (Streamlit UI)                           ║
║                                                                ║
║  Login  │  Upload  │  Analytics  │  Risk  │  Fraud  │  XAI    ║
║  Page   │  Page    │  Pages      │  Page  │  Page   │  Page   ║
╚═══════════════════════════════╤════════════════════════════════╝
                                │
╔═══════════════════════════════▼════════════════════════════════╗
║                     APPLICATION LAYER                          ║
║                         (app.py)                               ║
║                                                                ║
║  Authentication │ Session Mgmt │ RBAC │ Page Routing           ║
╚═══════════════════════════════╤════════════════════════════════╝
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
╔════════▼═══════╗  ╔═══════════▼══════╗  ╔═══════════▼══════╗
║  AUTH MODULE   ║  ║  ANALYTICS LAYER ║  ║  SECURITY LAYER  ║
║  (auth.py)     ║  ║                  ║  ║  (components.py) ║
║                ║  ║  ┌─────────────┐ ║  ║                  ║
║ - bcrypt hash  ║  ║  │fraud_ind.py │ ║  ║ - ID masking     ║
║ - rate limit   ║  ║  ├─────────────┤ ║  ║ - export logging ║
║ - lockout      ║  ║  │cust_risk.py │ ║  ║ - upload guard   ║
║ - session wipe ║  ║  ├─────────────┤ ║  ╚══════════════════╝
╚════════════════╝  ║  │explain_ai.py│ ║
                    ║  ├─────────────┤ ║
                    ║  │data_valid.py│ ║
                    ║  └─────────────┘ ║
                    ╚═════════╤════════╝
                              │
╔═════════════════════════════▼══════════════════════════════════╗
║                      DATABASE LAYER                            ║
║                       (database.py)                            ║
║                                                                ║
║  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  ║
║  │  upload_history│  │   customers    │  │  risk_analysis  │  ║
║  └────────────────┘  └────────────────┘  └─────────────────┘  ║
║  ┌────────────────┐  ┌────────────────┐                        ║
║  │fraud_indicators│  │   audit_log    │                        ║
║  └────────────────┘  └────────────────┘                        ║
║                                                                ║
║              SQLAlchemy ORM → SQLite                           ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Request Flow

### 1. Authentication Flow
```
User enters credentials
    │
    ▼
Check lockout state (st.session_state["lockouts"])
    │ Locked → return error with remaining time
    ▼
Fetch user from st.secrets["users"]
    │ Not found → record attempt + generic error
    ▼
bcrypt.checkpw(password, stored_hash)
    │ Wrong → record attempt + generic error (+ lockout if ≥5)
    ▼
Log LOGIN event to audit_log
    │
    ▼
Set session state: authenticated=True, username, role, last_activity
    │
    ▼
Redirect to dashboard
```

### 2. Upload & Validation Flow
```
User uploads file (CSV/XLSX)
    │
    ▼
Security checks:
  - os.path.basename (path traversal prevention)
  - extension whitelist (.csv, .xlsx only)
  - empty file guard (size == 0)
  - CSV formula injection sanitization (=, +, -, @ prefixed with ')
    │
    ▼
normalize_column_names() — maps raw headers to canonical names
    │
    ▼
validate_uploaded_dataset() — checks required columns, dtypes, quality
    │ Error → show validation report, block further processing
    ▼
prepare_uploaded_dataset() — applies 14 derived feature calculations
    │
    ▼
Store in st.session_state["uploaded_df"]
    │
    ▼
[Optional] Save to Database:
  ├── run_fraud_indicators()
  ├── ML pipeline.predict_proba()
  ├── generate_customer_risk_profile()
  └── save_dataset_to_db() → upload_history + customers + risk + fraud
    │
    ▼
Log UPLOAD_SAVE to audit_log
```

### 3. ML Prediction Flow
```
Customer DataFrame (cleaned + derived features)
    │
    ▼
Select feature_names from model_metadata.json
    │
    ▼
X = df[feature_names].fillna(0)
    │
    ▼
ImbPipeline.predict_proba(X) → default_probability [0,1]
    │
    ▼
Apply business threshold (from metadata)
    │
    ▼
Binary prediction + risk level assignment
```

### 4. XAI Explanation Flow
```
Trained ImbPipeline
    │
    ▼
get_shap_explainer(model, X_background)
  ├── TreeExplainer   (GradientBoosting / RandomForest)
  ├── LinearExplainer (LogisticRegression)
  └── KernelExplainer (fallback)
    │
    ▼
shap_values = explainer.shap_values(X_customer)
    │
    ▼
Shape normalization (2D/3D array → [n_samples, n_features])
    │
    ▼
generate_customer_explanation()
  ├── top_positive (risk increasing factors)
  ├── top_negative (risk reducing factors)
  └── natural_language_explanation (NL template)
    │
    ▼
Render in Streamlit with directional badges
```

### 5. Audit Logging Flow
```
Any security-relevant action:
  LOGIN / LOGOUT / UPLOAD_SAVE / EXPORT / DB_BACKUP / DB_RESTORE
    │
    ▼
log_audit_event(username, role, action, object_type, object_id, result, details)
    │
    ▼
INSERT into audit_log (non-blocking, catches its own exceptions)
    │
    ▼
Viewable in Database Management page (Admin only)
```

---

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | Main orchestrator — page routing, session management, RBAC guards |
| `auth.py` | Authentication, rate limiting, lockout, password validation |
| `app_config.py` | Page names, PATHS constants |
| `styles.py` | Design system, PALETTE, all HTML/CSS rendering helpers |
| `components.py` | Reusable UI components, ID masking, export logging |
| `data_loader.py` | Load CSV data and model pipeline |
| `data_validation.py` | Uploaded dataset quality checks |
| `data_validator.py` | Column normalisation, prepare_uploaded_dataset |
| `fraud_indicators.py` | 9 rule-based fraud indicator calculations |
| `customer_risk_analysis.py` | Weighted risk score, risk levels, risk reasons |
| `explainable_ai.py` | SHAP explanations, NL generation, global importance |
| `database.py` | All DB operations — CRUD, versioning, audit, backup |
| `charts.py` | Plotly chart builders |

---

## Data Models

### `upload_history`
| Column | Type | Description |
|---|---|---|
| upload_id | INTEGER PK | Auto-increment |
| filename | TEXT | Original file name |
| uploaded_by | TEXT | Username |
| uploaded_at | DATETIME | Timestamp |
| validation_status | TEXT | pass / warning / error |
| quality_score | FLOAT | 0–100 |
| total_rows | INTEGER | Row count |
| total_columns | INTEGER | Column count |
| dataset_version | INTEGER | Sequential version |
| is_active | BOOLEAN | Current active dataset |
| is_deleted | BOOLEAN | Soft delete flag |

### `customers`
| Column | Type | Description |
|---|---|---|
| customer_pk | INTEGER PK | Auto-increment |
| upload_id | INTEGER FK | Links to upload_history |
| customer_id | TEXT | Original customer ID |
| financial_attributes | JSON | All remaining features |

### `risk_analysis`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| upload_id | INTEGER FK | Links to upload_history |
| customer_id | TEXT | Customer identifier |
| overall_risk_score | FLOAT | 0–100 |
| risk_level | TEXT | Low / Moderate / High |
| confidence | TEXT | High / Medium / Low |
| component_scores | JSON | Dict of contribution_ columns |

### `fraud_indicators`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| upload_id | INTEGER FK | Links to upload_history |
| customer_id | TEXT | Customer identifier |
| fraud_score | FLOAT | 0–14 |
| fraud_level | TEXT | Low / Moderate / High |
| triggered_indicators | JSON | List of active flag names |
| indicator_count | INTEGER | Number of triggered flags |

### `audit_log`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| timestamp | DATETIME | Event time |
| username | TEXT | Acting user |
| role | TEXT | User role |
| action | TEXT | LOGIN / LOGOUT / UPLOAD_SAVE / EXPORT / … |
| object_type | TEXT | Dataset / System / File |
| object_id | TEXT | Related ID or name |
| result | TEXT | SUCCESS / FAILED |
| details | TEXT | Free-text detail |

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Security Controls                       │
├─────────────────────────────────────────────────────────┤
│ Layer          │ Control                                 │
│────────────────│─────────────────────────────────────── │
│ Authentication │ bcrypt hashing                         │
│                │ 5-attempt lockout (15 min)             │
│                │ Generic error messages                  │
│                │ Timing attack delay                     │
├────────────────│─────────────────────────────────────── │
│ Session        │ 30-min inactivity timeout              │
│                │ Comprehensive session wipe on logout    │
├────────────────│─────────────────────────────────────── │
│ RBAC           │ Admin / Analyst / Loan Officer         │
│                │ Page-level guards on all sensitive pages│
├────────────────│─────────────────────────────────────── │
│ File Upload    │ Extension whitelist                     │
│                │ Empty file guard                        │
│                │ Filename sanitisation                   │
│                │ CSV formula injection prevention        │
├────────────────│─────────────────────────────────────── │
│ Privacy        │ Customer ID masking (Loan Officers)    │
│                │ Export audit logging                    │
│                │ Export warning banner                   │
├────────────────│─────────────────────────────────────── │
│ Database       │ Backup path traversal prevention       │
│                │ Sanitized DB exception messages         │
│                │ SQLAlchemy ORM (no raw SQL)             │
└─────────────────────────────────────────────────────────┘
```
