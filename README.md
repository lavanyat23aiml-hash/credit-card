# CreditGuard — Enterprise Credit Risk Analytics Platform

> A production-ready, end-to-end financial analytics and machine learning platform for credit risk assessment, fraud screening, and portfolio management.

---

## 1. Project Overview

**CreditGuard** is a full-stack financial analytics system built for credit risk professionals. It combines classical data engineering, interpretable machine learning, transparent fraud screening, and a modern multi-role Streamlit dashboard to give financial institutions a complete view of customer credit risk.

The system ingests customer credit-card data, validates it, computes behavioural risk signals, scores fraud indicators, generates ML-based default probability predictions, and provides human-readable AI explanations — all within a secured, role-based access interface.

---

## 2. Problem Statement

Financial institutions lose significant capital when creditworthy customers are denied credit and when high-risk customers receive excessive exposure. The challenge is two-fold:

- **Under-rejection**: Approving customers who subsequently default.
- **Over-rejection**: Denying creditworthy customers, losing revenue and damaging relationships.

CreditGuard addresses this by providing analysts with a multi-layer risk assessment system combining rule-based fraud indicators, ML predictions, and explainable AI — supported by a full audit trail and role-gated access controls.

---

## 3. Solution Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    CreditGuard System                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   User ──► Authentication (bcrypt + rate-limit lockout)     │
│              │                                               │
│              ▼                                               │
│   Role-Based Access (Admin / Analyst / Loan Officer)         │
│              │                                               │
│              ▼                                               │
│   Upload & Validation ──► Formula injection sanitization     │
│              │                                               │
│              ▼                                               │
│   Database Layer (SQLAlchemy / SQLite)                       │
│         ┌────────────┐                                       │
│         │ Customers  │                                       │
│         │ Risk       │                                       │
│         │ Fraud      │                                       │
│         │ Audit Log  │                                       │
│         └────────────┘                                       │
│              │                                               │
│         ┌────┴──────────────────────┐                        │
│         ▼                           ▼                        │
│   ML Prediction               Fraud Engine                   │
│   (ImbPipeline + SMOTE)       (9 rule-based indicators)      │
│         │                           │                        │
│         └────────────┬──────────────┘                        │
│                      ▼                                       │
│              Risk Scoring System                             │
│              (Component-weighted 0-100 score)                │
│                      │                                       │
│                      ▼                                       │
│              XAI Explanation (SHAP)                          │
│                      │                                       │
│                      ▼                                       │
│              Reports & Export (Audited CSV)                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Features

| Feature | Description |
|---|---|
| 🔐 **Authentication** | bcrypt password hashing, rate limiting, 15-min lockout after 5 failures |
| 🧭 **RBAC** | Admin / Analyst / Loan Officer roles with page-level access control |
| 📤 **Upload & Validation** | CSV/XLSX, formula injection prevention, missing column detection |
| 💾 **Database Integration** | SQLite via SQLAlchemy — versioned uploads, soft delete, full history |
| 📊 **Portfolio Analytics** | Segmentation, repayment behaviour, default rate analysis |
| 🔍 **Fraud-Risk Indicators** | 9 transparent rule-based indicators, configurable thresholds |
| ⚠️ **Customer Risk Analysis** | Weighted component scoring, confidence levels, risk reasons |
| 🤖 **ML Prediction** | Cost-sensitive ImbPipeline with business-tuned threshold |
| 🧠 **Explainable AI** | SHAP-based feature contributions, NL explanations, portfolio view |
| 🎭 **Data Privacy** | Role-based Customer ID masking for Loan Officers |
| 📋 **Audit Logging** | All logins, uploads, exports, and DB changes are logged |
| ⏰ **Session Security** | 30-minute inactivity timeout, secure session wipe on logout |
| 📦 **Docker Ready** | Single-container deployment with non-root user and health check |

---

## 5. Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11 |
| **Web Framework** | Streamlit 1.40 |
| **Data** | Pandas 2.2, NumPy 1.26 |
| **Visualisation** | Plotly 5.24, Matplotlib 3.9 |
| **ML & Imbalance** | Scikit-learn 1.5, Imbalanced-learn 0.12 |
| **Explainability** | SHAP 0.46 |
| **Database** | SQLAlchemy 2.0, SQLite |
| **Security** | bcrypt 4.2 |
| **Serialization** | Joblib 1.4 |
| **Testing** | Pytest 8.3 (130 tests) |
| **Containerization** | Docker, Docker Compose |

---

## 6. ML Pipeline

The prediction pipeline was trained on the **UCI Default of Credit Card Clients Dataset** (30,000 records, Taiwan 2005):

```
Raw Features (23)
     │
     ▼
Feature Engineering (14 derived features)
     │
     ▼
ImbPipeline:
  ├── StandardScaler (numeric features)
  ├── SMOTE (class balancing on train set)
  └── Gradient Boosting Classifier (cost-sensitive)
     │
     ▼
Business Threshold Tuning
(maximizes recall for defaulters at controlled precision)
     │
     ▼
Output: default_probability [0–1], binary prediction
```

**Key metrics (held-out test set):**
- AUC-ROC: see `reports/model/model_comparison.csv`
- Threshold: see `models/creditguard_model_metadata.json`

---

## 7. Fraud Detection Logic

9 transparent rule-based indicators scored 0–14:

| Indicator | Threshold (High) | Weight |
|---|---|---|
| High Credit Utilisation | ≥ 90% | 2 pts |
| Repeated Payment Delays | ≥ 4 periods | 2 pts |
| Maximum Repayment Delay | ≥ 3 months | 2 pts |
| Low Repayment Ratio | < 10% | 2 pts |
| Zero-Payment Pattern | ≥ 4 months | 2 pts |
| Sudden Bill Spike | > 2× previous | 1 pt |
| Large Credit Exposure | ≥ 95th pctl + 70% util | 1 pt |
| Inconsistent Payments | CV ≥ 1.5 | 1 pt |
| Portfolio Outlier | ≥ 2 vars outside 3×IQR | 1 pt |

**Levels:** Low (0–2) · Moderate (3–5) · High (6+)

> ⚠️ This is a screening tool. Results are indicators, not confirmed fraud.

---

## 8. Risk Scoring System

The Customer Risk Analysis module computes a weighted composite score (0–100):

| Component | Weight | Features Used |
|---|---|---|
| ML Default Probability | 40% | All 23+ features |
| Payment Behaviour | 25% | PAY_0–PAY_6 history |
| Credit Utilisation | 20% | LIMIT_BAL, BILL_AMT |
| Repayment Ratio | 15% | PAY_AMT vs BILL_AMT |

**Risk Levels:** Low (<40) · Moderate (40–69) · High (70+)

---

## 9. Explainable AI (XAI)

The XAI module uses SHAP to explain every ML prediction:

- **Global View**: Top-10 most influential features across the portfolio (mean |SHAP|)
- **Customer View**: Feature-level contributions with natural language explanation
- **Directional Badges**: Each factor labelled as Risk Increasing 🔴 or Risk Reducing 🟢
- **Graceful Degradation**: Falls back cleanly if SHAP cannot explain a specific model type

---

## 10. Security Features

| Control | Implementation |
|---|---|
| Password hashing | bcrypt with per-user salt |
| Brute force protection | 5-attempt lockout for 15 minutes |
| Timing attack prevention | Constant-time delay for non-existent users |
| Session timeout | Auto-logout after 30 minutes of inactivity |
| File upload hardening | Extension whitelist, empty-file check, filename sanitisation |
| Formula injection prevention | Neutralises `=`, `+`, `-`, `@` prefixes in CSV fields |
| Customer ID masking | Loan Officers see `******345` instead of full IDs |
| Export audit logging | Every CSV download is logged with user, role, timestamp, row count |
| Backup path protection | Directory traversal prevented in database export |
| DB error sanitisation | Raw SQLAlchemy exceptions never reach the UI |

---

## 11. Installation Guide

### Prerequisites
- Python 3.11+ or Docker
- Git

### Option A: Local (Python)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/creditguard-credit-risk.git
cd creditguard-credit-risk

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure secrets
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
# Edit secrets.toml and set bcrypt password hashes (see Step 12)

# 5. Run the application
streamlit run app.py
```

### Option B: Docker

```bash
# 1. Clone the repository
git clone https://github.com/your-org/creditguard-credit-risk.git
cd creditguard-credit-risk

# 2. Configure secrets
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
# Edit secrets.toml with your password hashes

# 3. Build and run
docker compose up --build

# App available at http://localhost:8501
```

---

## 12. Running Instructions

### Start the application
```bash
streamlit run app.py
```

### Generate password hashes for new users
```bash
python scripts/generate_password_hash.py
```

### Run the test suite
```bash
# With PYTHONPATH set (required)
export PYTHONPATH=.         # Windows: $env:PYTHONPATH="."
pytest -v

# Security tests only
pytest tests/test_security.py -v
```

### Verify all modules compile
```bash
# Linux/Mac
python -m py_compile app.py dashboard/streamlit/*.py

# Windows PowerShell
Get-ChildItem -Path "dashboard\streamlit" -Filter "*.py" | ForEach-Object { python -m py_compile $_.FullName }
```

---

## 13. Demo Credentials

Configure `secrets.toml` with the following demo accounts:

| Role | Username | Default Password | Access |
|---|---|---|---|
| **Admin** | `admin` | Set in secrets.toml | All pages + DB management |
| **Analyst** | `analyst` | Set in secrets.toml | All analytical pages |
| **Loan Officer** | `loan_officer` | Set in secrets.toml | Explorer, Risk Analysis, Prediction |

> See `docs/demo_guide.md` for step-by-step demo workflows.

---

## 14. Future Improvements

| Area | Improvement |
|---|---|
| **Auth** | Password self-service reset, OAuth2/SSO integration |
| **Database** | PostgreSQL support for multi-user concurrent deployments |
| **ML** | Online retraining pipeline, model versioning, A/B testing |
| **XAI** | Counterfactual explanations ("what would it take to approve?") |
| **Alerts** | Email/Slack notifications for high-risk uploads |
| **API** | REST API layer for integration with core banking systems |
| **Deployment** | Kubernetes Helm chart for enterprise-scale deployments |
| **Reporting** | PDF export of individual customer risk reports |

---

## Project Structure

```
creditguard-credit-risk/
│
├── app.py                          # Main Streamlit application (12 pages)
├── requirements.txt                # Pinned Python dependencies
├── Dockerfile                      # Production Docker image
├── docker-compose.yml              # Single-service deployment
├── .env.example                    # Environment variable template
├── .gitignore                      # Excludes secrets, databases, caches
│
├── dashboard/streamlit/            # Application modules
│   ├── app_config.py               # Page constants and paths
│   ├── auth.py                     # Authentication and session security
│   ├── components.py               # Reusable UI components + ID masking
│   ├── customer_risk_analysis.py   # Risk scoring engine
│   ├── data_loader.py              # Data loading helpers
│   ├── data_validation.py          # Upload validation rules
│   ├── data_validator.py           # Column normalisation
│   ├── database.py                 # Database layer (SQLAlchemy)
│   ├── explainable_ai.py           # SHAP-based XAI module
│   ├── fraud_indicators.py         # Rule-based fraud screening
│   └── styles.py                   # Design system and theming
│
├── data/
│   ├── processed/                  # Cleaned dataset (creditguard_cleaned.csv)
│   ├── raw/                        # Original datasets (gitignored)
│   ├── backups/                    # Database backups (gitignored)
│   └── sample_upload_template.csv  # Demo upload file
│
├── models/
│   ├── creditguard_final_pipeline.joblib  # Trained ImbPipeline
│   └── creditguard_model_metadata.json    # Threshold and feature names
│
├── docs/
│   ├── architecture.md             # System architecture documentation
│   └── demo_guide.md               # Role-based demo workflows
│
├── reports/model/                  # Model comparison and feature importance CSVs
├── sql/                            # SQL analysis scripts
├── src/                            # Data engineering source modules
├── scripts/                        # Utility scripts
│   └── generate_password_hash.py   # bcrypt hash generator
└── tests/                          # 130-test pytest suite
```

---

## Author

**Lavanya T** — Data Analyst & ML Engineer  
Portfolio: [GitHub](https://github.com/lavanyat23aiml)

---

## License

This project is released under the [MIT License](LICENSE).  
It is an **educational and portfolio demonstration project**. Do not use for actual lending or credit decisions.
