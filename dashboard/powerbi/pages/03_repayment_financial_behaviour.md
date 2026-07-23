# Page 3: Repayment and Financial Behaviour

**Page Size**: 16:9 (1280x720)

## Main Visuals
### 1. Default Rate by Delayed-Payment Count
- **Type**: Clustered Column Chart
- **Axis**: `FactCreditCustomer[delayed_payment_count]`
- **Values**: `Overall Default Rate`

### 2. Default Rate by Maximum Delay
- **Type**: Clustered Column Chart
- **Axis**: `FactCreditCustomer[maximum_delay_months]`
- **Values**: `Overall Default Rate`

### 3. PAY_0 Risk Analysis
- **Type**: Clustered Column Chart
- **Axis**: `FactCreditCustomer[pay_0]` (or `RepaymentHistoryUnpivoted[Repayment Status]`)
- **Values**: `Overall Default Rate`

### 4. Monthly Bill Trend
- **Type**: Line Chart
- **Axis**: `BillAmountMonthly[Month Number]`
- **Values**: `Average(BillAmountMonthly[Bill Amount])`
- **Sorting**: Axis ascending 1->6

### 5. Monthly Payment Trend
- **Type**: Line Chart
- **Axis**: `PayAmountMonthly[Month Number]`
- **Values**: `Average(PayAmountMonthly[Pay Amount])`

### 6. Avg Bill vs Avg Payment
- **Type**: Line and Column Combo Chart
- **Values**: `Average Bill Amount`, `Average Payment Amount`

### 7. Credit Utilisation by Default Status
- **Type**: Clustered Bar Chart
- **Axis**: `DimDefaultStatus[default_label]`
- **Values**: `Average Credit Utilisation`

### 8. Payment-to-Bill Ratio by Default Status
- **Type**: Clustered Bar Chart
- **Axis**: `DimDefaultStatus[default_label]`
- **Values**: `Average Payment-to-Bill Ratio`

### 9. Delayed vs Non-Delayed Comparison
- **Type**: Clustered Column Chart
- **Axis**: `FactCreditCustomer[has_payment_delay]` (or calculated `Delay Status`)
- **Values**: `Overall Default Rate`, `Total Customers`
