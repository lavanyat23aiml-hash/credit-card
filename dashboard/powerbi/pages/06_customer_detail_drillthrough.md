# Page 6: Customer Detail (Drill-through)

**Page Type**: Hidden Page, Tooltip allowed
**Page Size**: Custom (e.g., standard 16:9 or custom for Tooltip ~300x200px. Create a separate small page for just the tooltip if desired).

## Configuration
- **Hide Page**: Yes
- **Drill-through field**: `FactCreditCustomer[id]`
- **Keep all filters**: Off (Show only the selected customer)

## Visuals
1. **Back Button**: Insert -> Buttons -> Back (Top-left corner)
2. **Customer Demographics Cards**: Use Card visuals for `age`, `sex_label`, `education_label`, `marriage_label`.
3. **Financials Cards**: `limit_bal`, `credit_utilisation_ratio`, `average_bill_amount`, `average_payment_amount`.
4. **Historical Delay Info**: `maximum_delay_months`, `delayed_payment_count`.
5. **Actual Outcome**: `default_label` (No predictive probability).

6. **6-Month Bill vs Payment Trend**
- **Type**: Clustered Column Chart or Line Chart
- **Source**: Directly from `FactCreditCustomer` columns (`bill_amt1`..`6`, `pay_amt1`..`6`) or the unpivoted query filtered by `id`.
- **Note**: The context is filtered down to a single `id` via drill-through.
