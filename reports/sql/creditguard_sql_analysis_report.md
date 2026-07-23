# CreditGuard SQL Analysis Report

## 1. Analysis Objective
To leverage SQLite to perform comprehensive business analysis on the CreditGuard dataset, evaluating risk across demographic, financial, and behavioral vectors without relying on complex machine learning models.

## 2. Database Overview
- **Database File:** `data/processed/creditguard.db`
- **Primary Table:** `credit_customers`
- **Total Records:** 30000
- **Total Defaulters:** 6636
- **Overall Default Rate:** 22.12%

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
- Age groups exhibit varying risk, with `60+` showing the highest default rate (33.33%).
- Education plays a role: `High school` category defaults at 29.17%.

### Repayment Risk
- Customers missing recent payments (PAY_0) have drastically increased default rates.
- The default rate scales monotonically with the number of delayed payments.

### Credit Limit Risk
- Customers with a `Low` credit limit have a default probability of 31.79%.

### High-Risk Segments
The highest absolute number of defaulters are found in the following segment:
- Age: 20-29
- Credit Limit: Low
- Education: University
- Delay Status: 1 (1 = Has Delay, 0 = No Delay)
- Defaulter Count: 450

## 5. Business Recommendations
1. Establish stricter monitoring for the 'Low' credit limit tier.
2. Implement early-warning triggers based on the very first delayed payment (PAY_0).
3. Allocate higher credit resources to demographics demonstrating consistently low default rates.

## 6. Limitations
- SQL analysis provides correlative insights but cannot capture non-linear relationships as effectively as Machine Learning.
- The definition of segments requires an arbitrary minimum cutoff (e.g., 100 customers) to avoid statistical noise.

## 7. Exported SQL Data
Multiple dashboard-ready CSV files have been exported to `data/processed/sql_outputs/` for use in Power BI.
