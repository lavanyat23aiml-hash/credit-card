# CreditGuard Exploratory Data Analysis Report

## Executive Summary
This report summarises the exploratory data analysis of the CreditGuard dataset. 
The overall default rate is 22.12%.

## Dataset Overview
- Total Records: 30000
- Target Imbalance: 23364 non-defaults vs 6636 defaults.

## Demographic Findings
- **Sex**: Male has the highest default rate (24.17%).
- **Education**: High school shows a higher risk (25.16%).
- **Marriage**: Others category has a default rate of 23.61%.
- **Age**: The 60+ age group is the most vulnerable.

## Credit Limit Findings
- Lower credit limit groups (Low) tend to default more frequently (31.79%).

## Repayment History Findings
- Customers with a maximum delay of 7 months have a default rate of 83.58%.
- High recent delay (PAY_0 = 7) strongly correlates with default (77.78%).

## High-Risk Customer Segments
Top highest risk segment:
- Age Group: 40-49
- Credit Limit: Low
- Education: University
- Has Delay: 1
- **Default Rate**: 55.31%

## Business Implications & Recommendations
- Target early interventions for customers missing their first payment.
- Adjust credit limits for high-risk demographic combinations.
- Features related to payment delays are highly predictive and should be focal points in model development.
