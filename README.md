# CreditGuard — Credit Default Risk Analytics and Prediction System

## Project Overview
CreditGuard is an end-to-end data analytics and machine-learning system designed to analyze customer credit-card repayment behavior, detect high-risk customer segments, and predict the probability of default. The project integrates data engineering, exploratory data analysis, SQL business analytics, machine learning model evaluation, Power BI visualization, and an interactive Streamlit application.

---

## Business Problem
Financial institutions face significant financial losses when customers fail to make required credit repayments. However, rejecting reliable customers unnecessarily can lead to lost revenue and damage customer relationships. 

The goal of CreditGuard is to analyze repayment behavior and develop a credit-risk prediction system that prioritizes identifying likely defaulters while minimizing unnecessary rejection of creditworthy customers.

---

## Project Objectives
- **Analyze Repayment Behavior:** Evaluate customer repayment history, credit limits, bill statements, and payment patterns.
- **Identify Risk Segments:** Segment customers to pinpoint high-risk demographics and financial behavioral groups.
- **Examine Key Metrics:** Evaluate relationships between credit limits, bill amounts, paid amounts, payment status, and default rates.
- **Machine Learning Classification:** Build, tune, and evaluate classification models to accurately predict credit default.
- **Handle Class Imbalance:** Apply advanced techniques (e.g., SMOTE, class weighting) to address imbalanced credit default data.
- **SQL Analytics:** Write structured SQL queries to answer critical business intelligence questions.
- **Interactive Dashboards:** Build an interactive Power BI dashboard for executive reporting and visual analytics.
- **Web Application:** Develop and deploy a user-friendly Streamlit web app for real-time risk predictions.
- **Comprehensive Documentation:** Maintain clear, modular code and end-to-end documentation on GitHub.

---

## Primary Users
- **Credit-Risk Analysts:** For evaluating default patterns and feature importance.
- **Financial Business Analysts:** For extracting insights on customer repayment behavior and portfolio health.
- **Risk-Management Teams:** For setting risk thresholds and policy guidelines.
- **Lending & Credit-Card Departments:** For informed credit allocation and limit adjustment.
- **Business Decision-Makers:** For executive-level overview via Power BI dashboards.

---

## Planned Technology Stack
- **Programming Language:** Python
- **Data Manipulation & Analysis:** Pandas, NumPy
- **Data Visualization:** Matplotlib, Plotly
- **Database & Querying:** SQL, SQLite, SQLAlchemy
- **Machine Learning & Modeling:** Scikit-learn, Imbalanced-learn, Joblib
- **Business Intelligence:** Power BI
- **Web Application Framework:** Streamlit
- **Testing & Quality Assurance:** Pytest
- **Version Control & Collaboration:** Git, GitHub

---

## Dataset Information
The project uses the **UCI Default of Credit Card Clients Dataset**:
- **Dataset Dimensions:** 30,000 customer records and 25 columns
- **Credit-Limit Information:** Amount of given credit (`LIMIT_BAL` in NT dollars)
- **Demographic Variables:** Gender (`SEX`), Education level (`EDUCATION`), Marital status (`MARRIAGE`), and Age (`AGE`)
- **Six Months of Repayment-Status History:** Past monthly payment status from April to September 2005 (`PAY_0` to `PAY_6`)
- **Six Months of Bill-Statement Amounts:** Monthly bill statement balances from April to September 2005 (`BILL_AMT1` to `BILL_AMT6`)
- **Six Months of Previous-Payment Amounts:** Amount paid each month from April to September 2005 (`PAY_AMT1` to `PAY_AMT6`)
- **Binary Default Target:** Binary default indicator (`default_payment_next_month`), where `1` indicates default in October 2005 and `0` indicates timely repayment.

---

## Planned Project Workflow
```
Business Understanding
       │
       ▼
Dataset Collection & Inspection
       │
       ▼
Data Cleaning & Preprocessing
       │
       ▼
Exploratory Data Analysis (EDA)
       │
       ▼
SQL Business Analysis
       │
       ▼
Feature Engineering
       │
       ▼
Model Development & Imbalance Handling
       │
       ▼
Model Evaluation & Tuning
       │
       ▼
Power BI Dashboard Creation
       │
       ▼
Streamlit Application Development
       │
       ▼
Testing & Verification
       │
       ▼
GitHub Documentation & Final Deployment
```

---

## Planned Folder Structure
```
creditguard-credit-risk/
│
├── data/
│   ├── raw/                  # Original raw datasets (unprocessed)
│   └── processed/            # Cleaned and engineered datasets
│
├── notebooks/                # Jupyter notebooks for EDA and experimentation
│
├── src/                      # Modular Python source code
│   ├── __init__.py           # Package initializer
│   ├── data_cleaning.py      # Data cleaning and preprocessing module
│   ├── eda.py                # Exploratory data analysis helpers
│   ├── feature_engineering.py# Feature creation and transformation
│   ├── train_model.py        # Model training, tuning, and evaluation
│   └── utils.py              # Utility helper functions
│
├── sql/                      # SQL scripts for database analysis
│   └── credit_risk_analysis.sql
│
├── dashboard/                # Dashboards and interactive apps
│   ├── powerbi/              # Power BI report files and assets
│   └── streamlit/            # Streamlit dashboard resources
│
├── models/                   # Serialized machine learning models (.joblib/.pkl)
├── reports/                  # Generated analysis reports and documentation
├── images/                   # Screenshots, plots, and visual assets
├── tests/                    # Unit tests for codebase verification
│
├── app.py                    # Main Streamlit web application
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── .gitignore                # Git ignore configuration
└── LICENSE                   # Project license file
```

---

## Current Development Status
- **Phase 1 Complete:** Project repository architecture, folder structure, environment configuration, dependency list, and base Streamlit setup initialized.
- **Phase 2 Complete:** Dataset collection, dynamic header inspection, target column standardization (`default_payment_next_month`), inspection report generation, and data understanding notebook setup.
- **Phase 3 Complete:** Data cleaning and feature engineering. Validated data integrity, applied categorical mapping, and engineered 14 new analytical features into `creditguard_cleaned.csv` and `creditguard_model_ready.csv`.
- **Phase 4 Complete:** Exploratory data analysis (EDA). Generated 18+ high-quality visualisations, extracted dashboard-ready CSV metrics, identified highest risk customer segments, and documented business insights in reports.
- **Phase 5 Complete:** SQL Business Analysis and Database Integration. Loaded the cleaned dataset into a SQLite database (`creditguard.db`). Created 35+ structured SQL queries and views to extract deep demographic, financial, and repayment insights. Exported 12 dashboard-ready CSV reports and generated automated SQL business reports.

---

## Future Phases
- **Phase 6 Complete:** Feature engineering and machine learning model development. Trained cost-sensitive classification models (Logistic Regression, Random Forest) utilizing class-weighting and SMOTE to handle the imbalanced dataset. Selected the optimal classification threshold based on illustrative business costs. Saved production-ready `ImbPipeline` and threshold metadata.
- **Phase 7 Complete (Preparation Phase):** Power BI Dashboard Preparation. Dynamically generated a standard Star Schema comprising a 30,000-row `FactCreditCustomer` table and 7 distinct `Dimension` tables. Provided comprehensive `DAX` code, power query steps, dashboard wireframes, and theme instructions. *Note: The final `.pbix` dashboard file is pending manual construction in Power BI Desktop by following the provided dashboard documentation.*
- **Phase 8 Complete:** Streamlit Analytics Application Implementation. Built a highly robust, 7-page local Streamlit dashboard (`app.py`) which acts as the **primary interactive interface** for the project. Features include Portfolio Analytics, High-Risk Customer Explorer, interactive visual segmentation, and an ML-powered Customer Risk Prediction engine. Run locally via `streamlit run app.py`. Cloud deployment is currently pending.
- **Phase 9 Complete:** Optional Power BI Support Package. An automated script generates a comprehensive manual-build package inside `dashboard/powerbi/`. This includes M scripts, DAX measures, Theme JSON, and Markdown blueprints. *Note: The Power BI deliverable is optional documentation; no `.pbix` file is generated or claimed, and the Streamlit app replaces it as the functional dashboard.*

---

## Author
**Lavanya T**
