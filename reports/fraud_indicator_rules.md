# CreditGuard — Fraud-Risk Indicator Rules

This report documents the transparent, rule-based screening layer designed to flag unusual credit and repayment patterns. 

> [!IMPORTANT]
> **This system is for screening only. It does not prove fraud.** All outputs are analytical indicators to identify customers whose behaviour may warrant manual review. Do not label customers as confirmed fraudsters.

---

## Screening Indicators Reference

### 1. High Credit Utilisation
- **High Flag:** `credit_utilisation_ratio >= 0.90` (2 points)
- **Moderate Flag:** `credit_utilisation_ratio >= 0.75 and < 0.90` (1 point)
- **Reason:** "Customer is using a very high proportion of the available credit limit."

### 2. Repeated Payment Delays
- **High Flag:** `delayed_payment_count >= 4` billing periods (2 points)
- **Moderate Flag:** `delayed_payment_count` between 2 and 3 (1 point)
- **Reason:** "Customer has delayed payments across several billing periods."

### 3. Maximum Repayment Delay
- **High Flag:** `maximum_delay_months >= 3` months (2 points)
- **Moderate Flag:** `maximum_delay_months == 2` months (1 point)
- **Reason:** "Customer has experienced a long repayment delay."

### 4. Low Repayment Ratio
- **High Flag:** `payment_to_bill_ratio < 0.10` and `total_bill_amount > 0` (2 points)
- **Moderate Flag:** `payment_to_bill_ratio >= 0.10 and < 0.25` (1 point)
- **Reason:** "Payments are very low compared with outstanding bills."

### 5. Zero-Payment Pattern
- **High Flag:** At least 4 months of zero payment with positive billed amounts (2 points)
- **Moderate Flag:** Exactly 3 months of zero payment with positive billed amounts (1 point)
- **Reason:** "Customer has multiple billing periods with no payment despite outstanding balances."

### 6. Sudden Bill Spike
- **Flag:** Consecutive monthly bill increases by > 2× and by at least 10,000 (1 point)
- **Reason:** "Customer shows an unusually sharp increase in billed amount."

### 7. Large Credit Exposure
- **Flag:** `limit_bal` above the portfolio 95th percentile AND utilisation is at least 0.70 (1 point)
- **Reason:** "Customer combines a large credit limit with high utilisation."

### 8. Inconsistent Repayment Behaviour
- **Flag:** Coefficient of variation (CV) of payment amounts >= 1.5 and average payment is positive (1 point)
- **Reason:** "Customer payment behaviour varies substantially across months."

### 9. Portfolio Outlier
- **Flag:** Customer has >= 2 variables outside 3× IQR range in the portfolio (1 point)
- **Variables Checked:** `limit_bal`, `average_bill_amount`, `average_payment_amount`, `credit_utilisation_ratio`, `payment_to_bill_ratio`, `delayed_payment_count`
- **Reason:** "Customer behaviour is statistically unusual compared with the current portfolio."

---

## Scoring and Action Matrix

The **Fraud-Risk Score** is the sum of the points triggered by the indicators above (maximum possible score is 14).

| Score Range | Indicator Level | Recommendation | Action |
|---|---|---|---|
| **0 – 2** | Low | No immediate action required. | Continue normal monitoring. |
| **3 – 5** | Moderate | Review recent payment behaviour. | Consider additional verification. |
| **6+** | High | Manual review recommended. | Review before approving additional credit exposure. |

---

## Graceful Degradation & Data Privacy
- **Missing Columns:** If the dataset lacks required columns, unavailable indicators are cleanly bypassed (returning `np.nan`), do not crash the app, and do not contribute to risk scores or reasons.
- **Session Memory:** All calculations run strictly in session memory. Flagged customer records are never logged or written permanently to disk. Session keys are cleared automatically on logout.
