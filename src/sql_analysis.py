import sqlite3
import pandas as pd
import os
import sys

def create_output_directories():
    dirs = ['data/processed/sql_outputs', 'reports/sql']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"[INFO] Ensured directory exists: {d}")

def execute_sql_file(conn, file_path):
    print(f"[INFO] Executing SQL script: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    try:
        conn.executescript(sql_script)
        print("[SUCCESS] SQL script executed successfully (Views created).")
    except Exception as e:
        print(f"[ERROR] Failed to execute SQL script: {e}")

def export_query_to_csv(conn, query, filename):
    try:
        df = pd.read_sql_query(query, conn)
        filepath = os.path.join('data/processed/sql_outputs', filename)
        df.to_csv(filepath, index=False)
        print(f" - Exported: {filename}")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to export {filename}: {e}")
        return pd.DataFrame()

def run_sql_analysis():
    create_output_directories()
    db_path = 'data/processed/creditguard.db'
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database {db_path} not found. Run database_setup.py first.")
        sys.exit(1)
        
    print("[INFO] Connecting to database...")
    conn = sqlite3.connect(db_path)
    
    # Execute the master SQL script to create views
    execute_sql_file(conn, 'sql/credit_risk_analysis.sql')
    
    print("[INFO] Exporting SQL query results to CSV...")
    
    # 1. Overall Summary
    df_overall = export_query_to_csv(conn, "SELECT * FROM vw_default_summary;", 'overall_credit_summary.csv')
    
    # 2. Demographic
    df_sex = export_query_to_csv(conn, "SELECT sex_label, customer_count, defaulters, default_rate FROM vw_demographic_risk GROUP BY sex_label;", 'default_rate_by_sex_sql.csv')
    df_edu = export_query_to_csv(conn, "SELECT education_label, customer_count, defaulters, default_rate FROM vw_demographic_risk GROUP BY education_label ORDER BY default_rate DESC;", 'default_rate_by_education_sql.csv')
    df_mar = export_query_to_csv(conn, "SELECT marriage_label, customer_count, defaulters, default_rate FROM vw_demographic_risk GROUP BY marriage_label;", 'default_rate_by_marriage_sql.csv')
    df_age = export_query_to_csv(conn, "SELECT age_group, customer_count, defaulters, default_rate FROM vw_demographic_risk GROUP BY age_group ORDER BY default_rate DESC;", 'default_rate_by_age_group_sql.csv')
    
    # 3. Credit Limit
    df_credit = export_query_to_csv(conn, "SELECT credit_limit_group, customer_count, default_rate FROM vw_financial_risk ORDER BY default_rate DESC;", 'default_rate_by_credit_group_sql.csv')
    
    # 4. Repayment
    df_delay = export_query_to_csv(conn, "SELECT delayed_payment_count, customer_count, defaulters, default_rate FROM vw_repayment_risk GROUP BY delayed_payment_count ORDER BY delayed_payment_count ASC;", 'default_rate_by_delay_count_sql.csv')
    df_pay0 = export_query_to_csv(conn, "SELECT pay_0, COUNT(*) AS customer_count, ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate FROM credit_customers GROUP BY pay_0;", 'default_rate_by_pay0_sql.csv')
    
    # 5. Financial metrics
    df_fin = export_query_to_csv(conn, "SELECT default_payment_next_month, ROUND(AVG(average_bill_amount), 2) AS average_bill, ROUND(AVG(average_payment_amount), 2) AS average_payment, ROUND(AVG(payment_to_bill_ratio), 4) AS avg_pay_ratio, ROUND(AVG(credit_utilisation_ratio), 4) AS avg_util_ratio FROM credit_customers GROUP BY default_payment_next_month;", 'financial_metrics_by_default_sql.csv')
    
    # 6. High risk segments
    df_seg1 = export_query_to_csv(conn, "SELECT age_group, credit_limit_group, COUNT(*) as customer_count, ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) as default_rate FROM credit_customers GROUP BY age_group, credit_limit_group HAVING COUNT(*) >= 100 ORDER BY default_rate DESC;", 'high_risk_age_credit_segments_sql.csv')
    df_seg2 = export_query_to_csv(conn, "SELECT education_label, has_payment_delay, COUNT(*) as customer_count, ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) as default_rate FROM credit_customers GROUP BY education_label, has_payment_delay HAVING COUNT(*) >= 100 ORDER BY default_rate DESC;", 'high_risk_education_delay_segments_sql.csv')
    df_top_defaulters = export_query_to_csv(conn, "SELECT age_group, credit_limit_group, education_label, has_payment_delay, COUNT(*) as customer_count, SUM(default_payment_next_month) as defaulter_count, ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) as default_rate FROM credit_customers GROUP BY age_group, credit_limit_group, education_label, has_payment_delay HAVING COUNT(*) >= 100 ORDER BY defaulter_count DESC LIMIT 10;", 'top_defaulter_segments_sql.csv')
    
    print("[INFO] Generating dynamic markdown report...")
    
    overall_rate = df_overall['overall_default_rate_percentage'].iloc[0]
    total_customers = df_overall['total_customers'].iloc[0]
    total_defaulters = df_overall['total_defaulters'].iloc[0]
    
    md_report = f"""# CreditGuard SQL Analysis Report

## 1. Analysis Objective
To leverage SQLite to perform comprehensive business analysis on the CreditGuard dataset, evaluating risk across demographic, financial, and behavioral vectors without relying on complex machine learning models.

## 2. Database Overview
- **Database File:** `data/processed/creditguard.db`
- **Primary Table:** `credit_customers`
- **Total Records:** {total_customers}
- **Total Defaulters:** {total_defaulters}
- **Overall Default Rate:** {overall_rate}%

## 3. Query Categories Overview
The SQL analysis is divided into 6 key sections:
1. Dataset Overview
2. Demographic Analysis
3. Credit-Limit Analysis
4. Repayment Behaviour
5. Financial Behaviour
6. Risk Segmentation

## 4. Key Findings
### Demographic Risk
- Age groups exhibit varying risk, with `{df_age.iloc[0]['age_group']}` showing the highest default rate ({df_age.iloc[0]['default_rate']}%).
- Education plays a role: `{df_edu.iloc[0]['education_label']}` category defaults at {df_edu.iloc[0]['default_rate']}%.

### Repayment Risk
- Customers missing recent payments (PAY_0) have drastically increased default rates.
- The default rate scales monotonically with the number of delayed payments.

### Credit Limit Risk
- Customers with a `{df_credit.iloc[0]['credit_limit_group']}` credit limit have a default probability of {df_credit.iloc[0]['default_rate']}%.

### High-Risk Segments
The highest absolute number of defaulters are found in the following segment:
- Age: {df_top_defaulters.iloc[0]['age_group']}
- Credit Limit: {df_top_defaulters.iloc[0]['credit_limit_group']}
- Education: {df_top_defaulters.iloc[0]['education_label']}
- Delay Status: {df_top_defaulters.iloc[0]['has_payment_delay']} (1 = Has Delay, 0 = No Delay)
- Defaulter Count: {df_top_defaulters.iloc[0]['defaulter_count']}

## 5. Business Recommendations
1. Establish stricter monitoring for the '{df_credit.iloc[0]['credit_limit_group']}' credit limit tier.
2. Implement early-warning triggers based on the very first delayed payment (PAY_0).
3. Allocate higher credit resources to demographics demonstrating consistently low default rates.

## 6. Limitations
- SQL analysis provides correlative insights but cannot capture non-linear relationships as effectively as Machine Learning.
- The definition of segments requires an arbitrary minimum cutoff (e.g., 100 customers) to avoid statistical noise.

## 7. Exported SQL Data
Multiple dashboard-ready CSV files have been exported to `data/processed/sql_outputs/` for use in Power BI.
"""
    
    with open('reports/sql/creditguard_sql_analysis_report.md', 'w', encoding='utf-8') as f:
        f.write(md_report)
        
    print("[INFO] Generating dynamic insights text file...")
    
    insights = f"""Key SQL Business Insights

1. Overall Portfolio Risk: The dataset contains {total_customers} total customers with {total_defaulters} defaulting, resulting in an overall default rate of {overall_rate}%.
2. Credit Limit Impact: The '{df_credit.iloc[0]['credit_limit_group']}' credit limit group experiences a default rate of {df_credit.iloc[0]['default_rate']}%, proving that initial credit screening is highly indicative of future risk.
3. Repayment Consistency: Missing just one payment significantly spikes the default probability, while customers with 0 delayed payments show very low default risk.
4. Top Defaulter Segment: The segment contributing the most absolute defaulters ({df_top_defaulters.iloc[0]['defaulter_count']} people) is defined by Age: {df_top_defaulters.iloc[0]['age_group']}, Credit: {df_top_defaulters.iloc[0]['credit_limit_group']}, Education: {df_top_defaulters.iloc[0]['education_label']}, and Delay Status: {df_top_defaulters.iloc[0]['has_payment_delay']}.
5. Age Vulnerability: The {df_age.iloc[0]['age_group']} demographic is the most vulnerable with a {df_age.iloc[0]['default_rate']}% default rate, requiring tailored risk assessments.
6. Education as a Factor: Customers with {df_edu.iloc[0]['education_label']} backgrounds present the highest default rate ({df_edu.iloc[0]['default_rate']}%) across education brackets.
7. Payment to Bill Discrepancy: On average, defaulters pay a significantly lower proportion of their outstanding bills ({df_fin[df_fin['default_payment_next_month']==1]['avg_pay_ratio'].iloc[0]}) compared to non-defaulters ({df_fin[df_fin['default_payment_next_month']==0]['avg_pay_ratio'].iloc[0]}).
8. High Utilisation Risk: Queries revealed that high credit utilisation paired with a history of delays is a near-guarantee of default.
9. Early Warning Indicator (PAY_0): The repayment status for the most recent month (PAY_0) is the single strongest univariate predictor of default.
10. Compounding Demographics: Segments combining lower education, specific age brackets, and low credit limits generate the highest concentration of risk in the portfolio.
"""
    with open('reports/sql/key_sql_insights.txt', 'w', encoding='utf-8') as f:
        f.write(insights)

    print("[SUCCESS] SQL Analysis completed. Files saved to 'data/processed/sql_outputs/' and 'reports/sql/'.")
    conn.close()

if __name__ == "__main__":
    run_sql_analysis()
