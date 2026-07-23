-- ==============================================================================
-- CREDITGUARD SQL BUSINESS ANALYSIS
-- Target Database: data/processed/creditguard.db
-- Table: credit_customers
-- ==============================================================================

-- ==========================================
-- 7. CREATE SQL VIEWS (Execute First)
-- ==========================================

DROP VIEW IF EXISTS vw_customer_risk_profile;
CREATE VIEW vw_customer_risk_profile AS
SELECT 
    id,
    age_group,
    sex_label,
    education_label,
    marriage_label,
    credit_limit_group,
    limit_bal,
    delayed_payment_count,
    maximum_delay_months,
    has_payment_delay,
    average_bill_amount,
    average_payment_amount,
    payment_to_bill_ratio,
    credit_utilisation_ratio,
    default_payment_next_month
FROM credit_customers;

DROP VIEW IF EXISTS vw_default_summary;
CREATE VIEW vw_default_summary AS
SELECT 
    COUNT(*) AS total_customers,
    SUM(default_payment_next_month) AS total_defaulters,
    COUNT(*) - SUM(default_payment_next_month) AS total_non_defaulters,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS overall_default_rate_percentage
FROM credit_customers;

DROP VIEW IF EXISTS vw_demographic_risk;
CREATE VIEW vw_demographic_risk AS
SELECT 
    age_group,
    sex_label,
    education_label,
    marriage_label,
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulters,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate
FROM credit_customers
GROUP BY age_group, sex_label, education_label, marriage_label;

DROP VIEW IF EXISTS vw_repayment_risk;
CREATE VIEW vw_repayment_risk AS
SELECT 
    delayed_payment_count,
    maximum_delay_months,
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulters,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate
FROM credit_customers
GROUP BY delayed_payment_count, maximum_delay_months;

DROP VIEW IF EXISTS vw_financial_risk;
CREATE VIEW vw_financial_risk AS
SELECT 
    credit_limit_group,
    COUNT(*) AS customer_count,
    AVG(average_bill_amount) AS avg_bill,
    AVG(average_payment_amount) AS avg_payment,
    AVG(credit_utilisation_ratio) AS avg_utilisation,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate
FROM credit_customers
GROUP BY credit_limit_group;


-- ==========================================
-- SECTION A: DATASET OVERVIEW
-- ==========================================

-- 1-4. Overall default summary
SELECT * FROM vw_default_summary;

-- 5. Average credit limit
SELECT ROUND(AVG(limit_bal), 2) AS average_credit_limit 
FROM credit_customers;

-- 6. Minimum and maximum age
SELECT MIN(age) AS min_age, MAX(age) AS max_age 
FROM credit_customers;

-- 7. Count of customers with payment delays
SELECT 
    COUNT(*) AS delayed_customers,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM credit_customers), 2) AS delayed_percentage
FROM credit_customers
WHERE has_payment_delay = 1;


-- ==========================================
-- SECTION B: DEMOGRAPHIC ANALYSIS
-- ==========================================

-- 8. Customer count and default rate by sex
SELECT 
    sex_label, 
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY sex_label;

-- 9. Customer count and default rate by education
SELECT 
    education_label, 
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY education_label
ORDER BY default_rate_percentage DESC;

-- 10. Customer count and default rate by marriage
SELECT 
    marriage_label, 
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY marriage_label;

-- 11. Customer count and default rate by age group
SELECT 
    age_group, 
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY age_group
ORDER BY default_rate_percentage DESC;


-- ==========================================
-- SECTION C: CREDIT-LIMIT ANALYSIS
-- ==========================================

-- 12. Default rate by credit-limit group
SELECT 
    credit_limit_group, 
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY credit_limit_group
ORDER BY default_rate_percentage DESC;

-- 13. Average credit limit by default status
SELECT 
    default_payment_next_month, 
    ROUND(AVG(limit_bal), 2) AS average_credit_limit
FROM credit_customers
GROUP BY default_payment_next_month;

-- 14. Top credit-limit groups by number of defaulters
SELECT 
    credit_limit_group, 
    SUM(default_payment_next_month) AS defaulter_count
FROM credit_customers
GROUP BY credit_limit_group
ORDER BY defaulter_count DESC;

-- 15. Default rate for customers above and below the median credit limit (Approx median NT$ 140000)
SELECT 
    CASE WHEN limit_bal >= 140000 THEN 'Above Median' ELSE 'Below Median' END AS limit_median_status,
    COUNT(*) AS customer_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY limit_median_status;


-- ==========================================
-- SECTION D: REPAYMENT BEHAVIOUR
-- ==========================================

-- 16. Default rate by delayed-payment count
SELECT 
    delayed_payment_count, 
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY delayed_payment_count
ORDER BY delayed_payment_count ASC;

-- 17. Default rate by maximum-delay months
SELECT 
    maximum_delay_months, 
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY maximum_delay_months
ORDER BY maximum_delay_months ASC;

-- 18. Default rate by PAY_0 status
SELECT 
    pay_0, 
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY pay_0
ORDER BY pay_0 ASC;

-- 19. Customers with no delay versus customers with at least one delay
SELECT 
    has_payment_delay, 
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY has_payment_delay;

-- 20. Customers with three or more delayed-payment months
SELECT 
    COUNT(*) AS high_delay_customers,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
WHERE delayed_payment_count >= 3;

-- 21. Average delay count by default status
SELECT 
    default_payment_next_month, 
    ROUND(AVG(delayed_payment_count), 2) AS average_delay_count
FROM credit_customers
GROUP BY default_payment_next_month;

-- 22. Most common repayment-status combinations (PAY_0 and PAY_2)
SELECT 
    pay_0, 
    pay_2, 
    COUNT(*) AS combination_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY pay_0, pay_2
ORDER BY combination_count DESC
LIMIT 10;


-- ==========================================
-- SECTION E: FINANCIAL BEHAVIOUR
-- ==========================================

-- 23. Average bill amount by default status
SELECT 
    default_payment_next_month, 
    ROUND(AVG(average_bill_amount), 2) AS average_bill
FROM credit_customers
GROUP BY default_payment_next_month;

-- 24. Average payment amount by default status
SELECT 
    default_payment_next_month, 
    ROUND(AVG(average_payment_amount), 2) AS average_payment
FROM credit_customers
GROUP BY default_payment_next_month;

-- 25. Average payment-to-bill ratio by default status
SELECT 
    default_payment_next_month, 
    ROUND(AVG(payment_to_bill_ratio), 4) AS average_pay_to_bill
FROM credit_customers
GROUP BY default_payment_next_month;

-- 26. Average credit-utilisation ratio by default status
SELECT 
    default_payment_next_month, 
    ROUND(AVG(credit_utilisation_ratio), 4) AS average_utilisation
FROM credit_customers
GROUP BY default_payment_next_month;

-- 27. Customers with high utilisation (> 80%) and payment delay
SELECT 
    COUNT(*) AS high_risk_utilisation_customers,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
WHERE credit_utilisation_ratio > 0.8 AND has_payment_delay = 1;

-- 28. Customers whose average bill exceeds their credit limit
SELECT 
    COUNT(*) AS over_limit_customers,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
WHERE average_bill_amount > limit_bal;

-- 29. Customers with zero previous payments across all 6 months
SELECT 
    COUNT(*) AS zero_payment_customers,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
WHERE total_payment_amount = 0;

-- 30. Customers with negative bill balances (overpaid)
SELECT 
    COUNT(*) AS negative_balance_customers,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
WHERE total_bill_amount < 0;


-- ==========================================
-- SECTION F: RISK SEGMENTATION
-- ==========================================

-- 31. High-risk segments by age group and credit-limit group
SELECT 
    age_group, 
    credit_limit_group,
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY age_group, credit_limit_group
HAVING COUNT(*) >= 100
ORDER BY default_rate_percentage DESC;

-- 32. High-risk segments by education and delay status
SELECT 
    education_label, 
    has_payment_delay,
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY education_label, has_payment_delay
HAVING COUNT(*) >= 100
ORDER BY default_rate_percentage DESC;

-- 33. High-risk segments by marriage and delayed-payment count
SELECT 
    marriage_label, 
    delayed_payment_count,
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY marriage_label, delayed_payment_count
HAVING COUNT(*) >= 100
ORDER BY default_rate_percentage DESC;

-- 34. Top 10 segments ranked by default rate (combining multiple features)
SELECT 
    age_group, 
    credit_limit_group,
    education_label,
    has_payment_delay,
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY age_group, credit_limit_group, education_label, has_payment_delay
HAVING COUNT(*) >= 100
ORDER BY default_rate_percentage DESC
LIMIT 10;

-- 35. Top 10 segments ranked by number of defaulters
SELECT 
    age_group, 
    credit_limit_group,
    education_label,
    has_payment_delay,
    COUNT(*) AS customer_count,
    SUM(default_payment_next_month) AS defaulter_count,
    ROUND(100.0 * SUM(default_payment_next_month) / COUNT(*), 2) AS default_rate_percentage
FROM credit_customers
GROUP BY age_group, credit_limit_group, education_label, has_payment_delay
HAVING COUNT(*) >= 100
ORDER BY defaulter_count DESC
LIMIT 10;
