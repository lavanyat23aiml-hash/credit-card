# CreditGuard Streamlit Application Guide

## Objective
To provide an interactive, browser-based interface for exploring the 30k CreditGuard portfolio dataset and generating live predictions using the saved Machine Learning models.

## How to Run Locally
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Run the application from the root project directory:
   ```bash
   streamlit run app.py
   ```
3. The app will launch in your default web browser (typically at `localhost:8501`).

## Application Pages
### 1. Home
Displays the business problem, project statistics, and educational disclaimers. 
*Note: This is an educational tool. Predictions should not dictate real lending decisions.*

### 2. Portfolio Analytics
Interactive dashboards filtering the 30,000-row `creditguard_cleaned.csv` dataset.
- Use the sidebar filters to isolate specific demographics (e.g., Male University Graduates).
- KPIs and Segment Tables will dynamically adjust.

### 3. Customer Risk Prediction
Allows you to build a single customer profile manually.
- **Workflow**: Enter demographics, credit limit, repayment delays, and bill/payment amounts.
- **Model Loading**: The model uses `@st.cache_resource` to keep the `.joblib` pipeline persistently in memory, ensuring fast predictions without reloading the 100MB+ object for every click.
- **Output**: Returns the estimated Probability of Default, categorized as Low/Moderate/High risk against the optimized model threshold.

### 4. Model Performance
Visualizes the results of Phase 6. Shows why Accuracy was rejected in favor of a cost-sensitive Threshold selection process that balances Precision and Recall to minimize business losses.

### 5. Project Documentation
End-to-end methodology covering Data Cleaning, SQL Analytics, ML modeling, and Power BI schemas.

## Error Handling
The app is built to fail gracefully:
- If model files (`models/creditguard_final_pipeline.joblib`) are missing, it throws a safe visual warning instead of crashing.
- If no data matches the selected filters on Page 2, a yellow warning banner appears instead of raising an empty DataFrame error.

## Limitations & Deployment
- The model uses historical 2005 data from Taiwan; macroeconomic conditions may have shifted.
- **Deployment**: The application is configured for local deployment only. Cloud deployment (e.g., Streamlit Community Cloud) is marked as pending.
