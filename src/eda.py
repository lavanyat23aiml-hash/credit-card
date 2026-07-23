import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import sys

# ---------------------------------------------------------
# Configuration and Styling
# ---------------------------------------------------------
PRIMARY_COLOR = '#1F77B4' # Corporate Blue
HIGHLIGHT_COLOR = '#FF7F0E' # Corporate Orange

plt.style.use('default')
mpl.rcParams['axes.facecolor'] = '#F8F9FA'
mpl.rcParams['figure.facecolor'] = '#FFFFFF'
mpl.rcParams['axes.edgecolor'] = '#D3D3D3'
mpl.rcParams['grid.color'] = '#E0E0E0'
mpl.rcParams['text.color'] = '#333333'
mpl.rcParams['axes.labelcolor'] = '#333333'
mpl.rcParams['xtick.color'] = '#333333'
mpl.rcParams['ytick.color'] = '#333333'
mpl.rcParams['font.size'] = 11

def create_directories():
    dirs = ['images/eda', 'reports/eda', 'data/processed/dashboard']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"[INFO] Ensured directory exists: {d}")

def validate_data(df):
    if df.empty:
        raise ValueError("Dataset is empty.")
    if 'default_payment_next_month' not in df.columns:
        raise ValueError("Target column 'default_payment_next_month' is missing.")
    
    unique_targets = df['default_payment_next_month'].unique()
    if not set(unique_targets).issubset({0, 1}):
        raise ValueError("Target contains values other than 0 and 1.")
    
    required_cols = [
        'age', 'age_group', 'limit_bal', 'credit_limit_group', 'sex_label',
        'education_label', 'marriage_label', 'average_bill_amount', 
        'average_payment_amount', 'payment_to_bill_ratio', 'credit_utilisation_ratio',
        'delayed_payment_count', 'maximum_delay_months'
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column missing: {col}")
    
    print("[SUCCESS] Data validation passed.")

def save_plot(filename):
    plt.tight_layout()
    plt.savefig(f"images/eda/{filename}", dpi=300, bbox_inches='tight')
    plt.close()

def plot_target_distribution(df):
    dist = df['default_payment_next_month'].value_counts()
    
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(['Non-Default (0)', 'Default (1)'], dist.values, color=[PRIMARY_COLOR, HIGHLIGHT_COLOR])
    ax.set_title("1. Target Class Distribution")
    ax.set_ylabel("Number of Customers")
    for i, v in enumerate(dist.values):
        ax.text(i, v + 200, str(v), ha='center', fontweight='bold')
    save_plot("target_distribution.png")

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.pie(dist.values, labels=['Non-Default (0)', 'Default (1)'], autopct='%1.1f%%', 
           colors=[PRIMARY_COLOR, HIGHLIGHT_COLOR], startangle=90, wedgeprops={'edgecolor': 'w'})
    ax.set_title("2. Default Percentage")
    save_plot("default_percentage.png")

def plot_univariate(df):
    # 3. Age distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df['age'], bins=20, color=PRIMARY_COLOR, edgecolor='w')
    ax.set_title("3. Age Distribution")
    ax.set_xlabel("Age")
    ax.set_ylabel("Frequency")
    save_plot("age_distribution.png")

    # 8. Credit-limit distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df['limit_bal'], bins=20, color=PRIMARY_COLOR, edgecolor='w')
    ax.set_title("8. Credit-Limit Distribution")
    ax.set_xlabel("Credit Limit (NT$)")
    ax.set_ylabel("Frequency")
    save_plot("credit_limit_distribution.png")

def plot_bivariate_default_rate(df, column, title, filename, sort=False):
    rate = df.groupby(column)['default_payment_next_month'].mean()
    if sort:
        rate = rate.sort_index()
    else:
        # standard categorical sort if possible or descending rate
        if rate.index.dtype == 'object':
            rate = rate.sort_values(ascending=False)
            
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(rate.index.astype(str), rate.values * 100, color=PRIMARY_COLOR)
    ax.set_title(title)
    ax.set_ylabel("Default Rate (%)")
    ax.set_xlabel(column.replace('_', ' ').title())
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # highlight max bar
    max_idx = rate.argmax()
    ax.patches[max_idx].set_facecolor(HIGHLIGHT_COLOR)

    for i, v in enumerate(rate.values):
        ax.text(i, v * 100 + 0.5, f"{v*100:.1f}%", ha='center', fontsize=9)
    plt.xticks(rotation=45, ha='right')
    save_plot(filename)
    return rate

def plot_bivariate(df):
    rates = {}
    rates['age_group'] = plot_bivariate_default_rate(df, 'age_group', "4. Default Rate by Age Group", "default_rate_by_age_group.png", sort=True)
    rates['sex_label'] = plot_bivariate_default_rate(df, 'sex_label', "5. Default Rate by Sex", "default_rate_by_sex.png")
    rates['education_label'] = plot_bivariate_default_rate(df, 'education_label', "6. Default Rate by Education", "default_rate_by_education.png")
    rates['marriage_label'] = plot_bivariate_default_rate(df, 'marriage_label', "7. Default Rate by Marriage", "default_rate_by_marriage.png")
    rates['credit_limit_group'] = plot_bivariate_default_rate(df, 'credit_limit_group', "9. Default Rate by Credit Limit Group", "default_rate_by_credit_group.png", sort=True)
    rates['delayed_payment_count'] = plot_bivariate_default_rate(df, 'delayed_payment_count', "10. Default Rate by Delayed Payment Count", "default_rate_by_delay_count.png", sort=True)
    rates['maximum_delay_months'] = plot_bivariate_default_rate(df, 'maximum_delay_months', "11. Default Rate by Maximum Delay Months", "default_rate_by_maximum_delay.png", sort=True)
    rates['pay_0'] = plot_bivariate_default_rate(df, 'pay_0', "12. PAY_0 (Recent Repayment) Default Rate Comparison", "pay_0_default_rate_comparison.png", sort=True)
    
    return rates

def plot_financials(df):
    metrics = {
        'average_bill_amount': ("13. Average Bill Amount by Default Status", "average_bill_amount_by_default.png"),
        'average_payment_amount': ("14. Average Payment Amount by Default Status", "average_payment_amount_by_default.png"),
        'payment_to_bill_ratio': ("15. Payment-to-Bill Ratio by Default Status", "payment_to_bill_ratio_by_default.png"),
        'credit_utilisation_ratio': ("16. Credit Utilisation Ratio by Default Status", "credit_utilisation_ratio_by_default.png")
    }
    
    fin_summary = df.groupby('default_payment_next_month')[list(metrics.keys())].mean()
    
    for col, (title, filename) in metrics.items():
        fig, ax = plt.subplots(figsize=(6, 5))
        vals = fin_summary[col].values
        ax.bar(['Non-Default', 'Default'], vals, color=[PRIMARY_COLOR, HIGHLIGHT_COLOR])
        ax.set_title(title)
        ax.set_ylabel(col.replace('_', ' ').title())
        for i, v in enumerate(vals):
            ax.text(i, v + (v * 0.02), f"{v:.2f}", ha='center')
        save_plot(filename)
        
    return fin_summary

def plot_correlation(df):
    num_cols = ['limit_bal', 'age', 'average_bill_amount', 'average_payment_amount', 
                'payment_to_bill_ratio', 'credit_utilisation_ratio', 'delayed_payment_count',
                'maximum_delay_months', 'default_payment_next_month']
    corr = df[num_cols].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    cax = ax.matshow(corr, cmap='Blues')
    fig.colorbar(cax)
    
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha='left')
    plt.yticks(range(len(corr.columns)), corr.columns)
    
    for (i, j), z in np.ndenumerate(corr):
        ax.text(j, i, '{:0.2f}'.format(z), ha='center', va='center', 
                color='white' if abs(z) > 0.5 else 'black', fontsize=8)
                
    ax.set_title("17. Correlation Heatmap for Numeric Variables", pad=20)
    save_plot("correlation_heatmap.png")

def identify_high_risk_segments(df):
    # Combinations of age, credit limit, education, etc.
    segments = df.groupby(['age_group', 'credit_limit_group', 'education_label', 'has_payment_delay']).agg(
        total_customers=('id', 'count'),
        defaulters=('default_payment_next_month', 'sum')
    ).reset_index()
    
    segments['default_rate'] = segments['defaulters'] / segments['total_customers']
    
    # Filter min 100 customers
    valid_segments = segments[segments['total_customers'] >= 100].copy()
    
    # Rank
    valid_segments = valid_segments.sort_values(by=['default_rate', 'defaulters', 'total_customers'], ascending=[False, False, False])
    top_10 = valid_segments.head(10)
    
    # Plot top 10
    fig, ax = plt.subplots(figsize=(10, 6))
    
    labels = []
    for _, row in top_10.iterrows():
        labels.append(f"{row['age_group']} | {row['credit_limit_group']} | {row['education_label']} | Delay:{row['has_payment_delay']}")
        
    ax.barh(labels[::-1], top_10['default_rate'][::-1] * 100, color=HIGHLIGHT_COLOR)
    ax.set_title("18. Top High-Risk Customer Segments (>100 customers)")
    ax.set_xlabel("Default Rate (%)")
    
    for i, v in enumerate(top_10['default_rate'][::-1]):
        ax.text(v * 100 + 0.5, i, f"{v*100:.1f}%", va='center', fontsize=9)
        
    save_plot("top_high_risk_segments.png")
    return top_10

def generate_reports(df, rates, fin_summary, top_segments):
    overall_default_rate = df['default_payment_next_month'].mean()
    
    # Markdown report
    md_content = f"""# CreditGuard Exploratory Data Analysis Report

## Executive Summary
This report summarises the exploratory data analysis of the CreditGuard dataset. 
The overall default rate is {overall_default_rate*100:.2f}%.

## Dataset Overview
- Total Records: {len(df)}
- Target Imbalance: {df['default_payment_next_month'].value_counts()[0]} non-defaults vs {df['default_payment_next_month'].value_counts()[1]} defaults.

## Demographic Findings
- **Sex**: {rates['sex_label'].idxmax()} has the highest default rate ({rates['sex_label'].max()*100:.2f}%).
- **Education**: {rates['education_label'].idxmax()} shows a higher risk ({rates['education_label'].max()*100:.2f}%).
- **Marriage**: {rates['marriage_label'].idxmax()} category has a default rate of {rates['marriage_label'].max()*100:.2f}%.
- **Age**: The {rates['age_group'].idxmax()} age group is the most vulnerable.

## Credit Limit Findings
- Lower credit limit groups ({rates['credit_limit_group'].idxmax()}) tend to default more frequently ({rates['credit_limit_group'].max()*100:.2f}%).

## Repayment History Findings
- Customers with a maximum delay of {rates['maximum_delay_months'].idxmax()} months have a default rate of {rates['maximum_delay_months'].max()*100:.2f}%.
- High recent delay (PAY_0 = {rates['pay_0'].idxmax()}) strongly correlates with default ({rates['pay_0'].max()*100:.2f}%).

## High-Risk Customer Segments
Top highest risk segment:
- Age Group: {top_segments.iloc[0]['age_group']}
- Credit Limit: {top_segments.iloc[0]['credit_limit_group']}
- Education: {top_segments.iloc[0]['education_label']}
- Has Delay: {top_segments.iloc[0]['has_payment_delay']}
- **Default Rate**: {top_segments.iloc[0]['default_rate']*100:.2f}%

## Business Implications & Recommendations
- Target early interventions for customers missing their first payment.
- Adjust credit limits for high-risk demographic combinations.
- Features related to payment delays are highly predictive and should be focal points in model development.
"""
    with open('reports/eda/creditguard_eda_report.md', 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    # Text insights
    insights = f"""Key Business Insights

1. Overall Default Risk: {overall_default_rate*100:.1f}% of the portfolio defaulted next month, representing a significant baseline risk.
2. The First Missed Payment (PAY_0) is Critical: Customers with a recent delay (PAY_0={rates['pay_0'].idxmax()}) have a huge default rate of {rates['pay_0'].max()*100:.1f}%. Immediate intervention here is crucial.
3. Credit Limit as a Proxy for Risk: Customers in the {rates['credit_limit_group'].idxmax()} bracket default at {rates['credit_limit_group'].max()*100:.1f}%, indicating strict initial screening reduces risk.
4. Age Vulnerability: The {rates['age_group'].idxmax()} group experiences the highest default rate ({rates['age_group'].max()*100:.1f}%), suggesting a need for tailored financial products for this demographic.
5. Education Factors: {rates['education_label'].idxmax()} graduates show a default rate of {rates['education_label'].max()*100:.1f}%.
6. Delayed Payment Accumulation: As delayed payment counts increase, default probability rises sharply. Maximum delays of {rates['maximum_delay_months'].idxmax()} months result in {rates['maximum_delay_months'].max()*100:.1f}% default rate.
7. Payment to Bill Ratio: Defaulters tend to pay a significantly lower portion of their bills compared to non-defaulters.
8. Gender Risk Profile: {rates['sex_label'].idxmax()} customers default at {rates['sex_label'].max()*100:.1f}%, compared to a lower rate for others.
9. Marriage Status Risk: {rates['marriage_label'].idxmax()} individuals have a default rate of {rates['marriage_label'].max()*100:.1f}%.
10. Compounded Risk Segment: The highest risk group (>100 customers) is "{top_segments.iloc[0]['age_group']}", "{top_segments.iloc[0]['credit_limit_group']}", "{top_segments.iloc[0]['education_label']}" with delays, reaching a massive {top_segments.iloc[0]['default_rate']*100:.1f}% default probability.
"""
    with open('reports/eda/key_business_insights.txt', 'w', encoding='utf-8') as f:
        f.write(insights)

    print("[SUCCESS] Generated reports and insights.")

def main():
    print("[INFO] Starting Exploratory Data Analysis...")
    create_directories()
    
    file_path = 'data/processed/creditguard_cleaned.csv'
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    df = pd.read_csv(file_path)
    validate_data(df)
    
    # Visualisations
    print("[INFO] Generating visualisations...")
    plot_target_distribution(df)
    plot_univariate(df)
    rates = plot_bivariate(df)
    fin_summary = plot_financials(df)
    plot_correlation(df)
    top_segments = identify_high_risk_segments(df)
    
    # Dashboards Data
    print("[INFO] Saving dashboard CSV tables...")
    rates['sex_label'].to_csv('data/processed/dashboard/default_rate_by_sex.csv')
    rates['education_label'].to_csv('data/processed/dashboard/default_rate_by_education.csv')
    rates['marriage_label'].to_csv('data/processed/dashboard/default_rate_by_marriage.csv')
    rates['age_group'].to_csv('data/processed/dashboard/default_rate_by_age_group.csv')
    rates['credit_limit_group'].to_csv('data/processed/dashboard/default_rate_by_credit_group.csv')
    rates['delayed_payment_count'].to_csv('data/processed/dashboard/default_rate_by_delay_count.csv')
    rates['maximum_delay_months'].to_csv('data/processed/dashboard/default_rate_by_maximum_delay.csv')
    rates['pay_0'].to_csv('data/processed/dashboard/default_rate_by_pay0.csv')
    fin_summary.to_csv('data/processed/dashboard/financial_metrics_by_default.csv')
    top_segments.to_csv('data/processed/dashboard/high_risk_segments.csv', index=False)
    
    # Reports
    print("[INFO] Generating final reports...")
    generate_reports(df, rates, fin_summary, top_segments)
    
    print("[SUCCESS] Phase 4 EDA completed successfully.")

if __name__ == "__main__":
    main()
