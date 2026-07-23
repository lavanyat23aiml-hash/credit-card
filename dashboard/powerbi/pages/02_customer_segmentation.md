# Page 2: Customer Segmentation

**Page Size**: 16:9 (1280x720)

## Main Visuals
### 1. Default Rate by Age Group
- **Type**: Clustered Column Chart
- **Axis**: `DimAgeGroup[age_group]`
- **Values**: `Overall Default Rate`

### 2. Default Rate by Credit Limit Group
- **Type**: Clustered Column Chart
- **Axis**: `DimCreditLimitGroup[credit_limit_group]`
- **Values**: `Overall Default Rate`

### 3. Default Rate by Education
- **Type**: Clustered Bar Chart
- **Axis**: `DimEducation[education_label]`
- **Values**: `Overall Default Rate`

### 4. Default Rate by Marriage
- **Type**: Clustered Bar Chart
- **Axis**: `DimMarriage[marriage_label]`
- **Values**: `Overall Default Rate`

### 5. Default Rate by Sex
- **Type**: Donut Chart
- **Legend**: `DimSex[sex_label]`
- **Values**: `Overall Default Rate`

### 6. Customer Count by Segment
- **Type**: Clustered Column Chart
- **Axis**: `DimAgeGroup[age_group]`
- **Values**: `Total Customers`

### 7. Defaulter Count by Segment
- **Type**: Clustered Column Chart
- **Axis**: `DimAgeGroup[age_group]`
- **Values**: `Total Defaulters`

### 8. High-Risk Segment Table
- **Type**: Table
- **Columns** (in order): 
  - `DimAgeGroup[age_group]`
  - `DimCreditLimitGroup[credit_limit_group]`
  - `DimEducation[education_label]`
  - `DimMarriage[marriage_label]`
  - `FactCreditCustomer[has_payment_delay]` (or calculated column)
  - `Total Customers`
  - `Total Defaulters`
  - `Overall Default Rate`
- **Visual Level Filter**: `Total Customers >= 30`
- **Conditional Formatting**: Background color on `Overall Default Rate` (e.g., Green <= 15%, Orange 15-30%, Red > 30%)
