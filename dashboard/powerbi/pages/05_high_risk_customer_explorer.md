# Page 5: High-Risk Customer Explorer

**Page Size**: 16:9 (1280x720)

## Slicers
- **Default Status** -> `DimDefaultStatus[default_label]`
- **Delay Status** -> `FactCreditCustomer[has_payment_delay]` (or calculated column)
- **Delayed-Payment Count** -> `FactCreditCustomer[delayed_payment_count]` (Between mode)
- **Maximum Delay** -> `FactCreditCustomer[maximum_delay_months]` (Between mode)
- **Age Group** -> `DimAgeGroup[age_group]`
- **Credit Limit Group** -> `DimCreditLimitGroup[credit_limit_group]`
- **Education** -> `DimEducation[education_label]`
- **Credit Utilisation** -> `FactCreditCustomer[credit_utilisation_ratio]` (Between mode)
- **Search by ID** -> `FactCreditCustomer[id]` (Text/Numeric search mode)

## Main Visuals
### 1. Detailed Customer Table
- **Type**: Table
- **Columns** (Exact Order):
  - `FactCreditCustomer[id]`
  - `FactCreditCustomer[age]`
  - `DimAgeGroup[age_group]`
  - `DimSex[sex_label]`
  - `DimEducation[education_label]`
  - `DimMarriage[marriage_label]`
  - `FactCreditCustomer[limit_bal]`
  - `DimCreditLimitGroup[credit_limit_group]`
  - `FactCreditCustomer[delayed_payment_count]`
  - `FactCreditCustomer[maximum_delay_months]`
  - `FactCreditCustomer[credit_utilisation_ratio]`
  - `FactCreditCustomer[average_bill_amount]`
  - `FactCreditCustomer[average_payment_amount]`
  - `FactCreditCustomer[payment_to_bill_ratio]`
  - `DimDefaultStatus[default_label]`
- **Conditional Formatting**:
  - `credit_utilisation_ratio`: Background color scale (Red > 0.7)
  - `maximum_delay_months`: Data bars (Red for 3+)
  - Row-level tint: Background rule on `id` column -> if `default_label = "Defaulter"` then light red tint.
- **Drill-through**: Ensure drill-through is configured to point to `Customer Detail`.
- **Tooltip**: Set Report Page Tooltip to a hidden page showing Bill Trend.
