# CreditGuard — Demo Guide

This guide walks through the complete CreditGuard demo workflow for each role. Use it to showcase the platform to stakeholders or during portfolio presentations.

---

## Prerequisites

1. Application is running: `streamlit run app.py`
2. `secrets.toml` is configured with three demo accounts:

```toml
[users.admin]
name = "CreditGuard Administrator"
password_hash = "<bcrypt hash of your admin password>"
role = "Admin"

[users.analyst]
name = "Credit Risk Analyst"
password_hash = "<bcrypt hash of your analyst password>"
role = "Analyst"

[users.loan_officer]
name = "Loan Officer"
password_hash = "<bcrypt hash of your loan_officer password>"
role = "Loan Officer"
```

Generate hashes: `python scripts/generate_password_hash.py`

---

## Sample Dataset

The file `data/sample_upload_template.csv` is a 50-row synthetic dataset with all required columns, suitable for demonstrating the full upload → analysis → export workflow.

---

## Demo Workflow 1 — Admin

**Goal:** Show full administrative control, database management, and audit visibility.

### Step-by-step

| Step | Action | Page |
|---|---|---|
| 1 | Log in as `admin` | Login |
| 2 | Navigate to **Executive Overview** | Home |
| 3 | Review KPI cards: total customers, default rate, avg risk score | Home |
| 4 | Go to **Data Upload & Validation** | Upload |
| 5 | Upload `data/sample_upload_template.csv` | Upload |
| 6 | Review validation results (pass/warning status) | Upload |
| 7 | Click **Save to Database** | Upload |
| 8 | Navigate to **Fraud-Risk Indicators** | Fraud |
| 9 | Adjust a threshold via the Admin panel | Fraud |
| 10 | Navigate to **Customer Risk Analysis** | Risk |
| 11 | Select a high-risk customer and view SHAP explanation | Risk |
| 12 | Navigate to **Explainable AI** | XAI |
| 13 | Review global feature importance chart | XAI |
| 14 | Navigate to **Database Management** | Database |
| 15 | View upload history and audit log | Database |
| 16 | Export the database as a backup | Database |
| 17 | Log out | Sidebar |

**Key talking points:**
- `admin` can access every page including DB Management
- Audit log shows every login, upload, and export event
- Threshold customisation is Admin-only

---

## Demo Workflow 2 — Analyst

**Goal:** Show the analytical workflow: upload, validate, analyse, and export.

### Step-by-step

| Step | Action | Page |
|---|---|---|
| 1 | Log in as `analyst` | Login |
| 2 | Navigate to **Data Upload & Validation** | Upload |
| 3 | Upload `data/sample_upload_template.csv` | Upload |
| 4 | Review quality score and warnings | Upload |
| 5 | Click **Use Temporarily** (no DB save needed for demo) | Upload |
| 6 | Navigate to **Customer Segmentation** | Segment |
| 7 | Filter by education or age group | Segment |
| 8 | Navigate to **Repayment & Financial Behaviour** | Finance |
| 9 | Show payment pattern trends | Finance |
| 10 | Navigate to **Fraud-Risk Indicators** | Fraud |
| 11 | Review high-fraud customers | Fraud |
| 12 | Navigate to **High-Risk Customer Explorer** | Explorer |
| 13 | Search for a specific Customer ID | Explorer |
| 14 | Download results as CSV | Explorer |
| 15 | Observe audit warning banner on export | Explorer |
| 16 | Log out | Sidebar |

**Key talking points:**
- Analyst cannot access Database Management
- Export triggers audit logging and warning banner
- All Customer IDs are visible in full (Analyst privilege)

---

## Demo Workflow 3 — Loan Officer

**Goal:** Show restricted read-only access with privacy masking.

### Step-by-step

| Step | Action | Page |
|---|---|---|
| 1 | Log in as `loan_officer` | Login |
| 2 | Attempt to navigate to **Data Upload** | Upload |
| 3 | Observe **Access Denied** page | Access Denied |
| 4 | Navigate to **Customer Risk Analysis** | Risk |
| 5 | Note that Customer IDs are masked: `******345` | Risk |
| 6 | Navigate to **High-Risk Customer Explorer** | Explorer |
| 7 | Search for a customer — IDs remain masked | Explorer |
| 8 | Navigate to **Customer Risk Prediction** | Predict |
| 9 | Enter manual feature values and get a prediction | Predict |
| 10 | Log out | Sidebar |

**Key talking points:**
- Loan Officers cannot upload, run model performance analysis, or access the database
- Customer IDs are automatically masked to protect privacy
- Loan Officers can still run individual predictions safely

---

## Feature Demonstration Checklist

| Feature | Demonstrated In |
|---|---|
| bcrypt authentication | Login (try a wrong password) |
| Rate limiting | Login (fail 5 times) |
| Session timeout | Leave app idle for 30 min |
| RBAC page guards | Loan Officer → Upload page |
| File upload security | Upload an empty or .txt file |
| Formula injection | Upload a CSV with `=SUM(...)` in a cell |
| Customer ID masking | Risk Analysis as Loan Officer |
| Export audit logging | Explorer → Download CSV |
| Fraud indicators | Fraud page with uploaded data |
| SHAP explanations | XAI page → select a customer |
| Database management | Database page (Admin only) |
| Audit log viewer | Database page → Audit Log tab |

---

## Troubleshooting

| Issue | Resolution |
|---|---|
| Login fails immediately | Check that `secrets.toml` has correct bcrypt hashes |
| Upload shows error | Ensure CSV has required columns (see `sample_upload_template.csv` for reference) |
| XAI page is blank | The model must be loadable from `models/creditguard_final_pipeline.joblib` |
| Database page missing | Only visible to Admin role |
| Docker container unhealthy | Ensure `curl` is available in the image and port 8501 is not blocked |
