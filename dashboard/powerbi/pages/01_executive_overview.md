# Page 1: Executive Overview

**Page Size**: 16:9 (1280x720)

## Slicers (Global, synced across Pages 1-3, 5)
- **Age Group** (Dropdown) -> `DimAgeGroup[age_group]`
- **Sex** (Dropdown) -> `DimSex[sex_label]`
- **Education** (Dropdown) -> `DimEducation[education_label]`
- **Marriage** (Dropdown) -> `DimMarriage[marriage_label]`
- **Credit Limit Group** (Dropdown) -> `DimCreditLimitGroup[credit_limit_group]`
- **Default Status** (Dropdown) -> `DimDefaultStatus[default_label]`

## KPI Cards (Top Row)
1. **Total Customers**: Card visual, Value: `Total Customers`
2. **Total Defaulters**: Card visual, Value: `Total Defaulters`, Color: Red accent
3. **Overall Default Rate**: Card visual, Value: `Overall Default Rate`, Color: Orange/Red accent
4. **Average Credit Limit**: Card visual, Value: `Average Credit Limit`
5. **Customers With Payment Delay**: Card visual, Value: `Customers With Payment Delay`
6. **Average Credit Utilisation**: Card visual, Value: `Average Credit Utilisation`

## Main Visuals
### 1. Default Rate by Age Group
- **Type**: Clustered Column Chart
- **Title**: Default Rate by Age Group
- **Source**: `DimAgeGroup` and `_Measures`
- **Axis**: `DimAgeGroup[age_group]`
- **Values**: `Overall Default Rate`
- **Sorting**: Axis ascending (by `Age Group Sort`)
- **Data Labels**: On, Percentage
- **Tooltip**: `Total Customers`, `Total Defaulters`
- **Position**: Top-left quadrant

### 2. Default Rate by Credit Limit Group
- **Type**: Clustered Column Chart
- **Title**: Default Rate by Credit Limit Group
- **Axis**: `DimCreditLimitGroup[credit_limit_group]`
- **Values**: `Overall Default Rate`
- **Sorting**: Axis ascending (by `Credit Limit Group Sort`)
- **Position**: Top-right quadrant

### 3. Default Rate by Sex
- **Type**: Donut Chart
- **Title**: Default Rate by Sex
- **Legend**: `DimSex[sex_label]`
- **Values**: `Overall Default Rate`
- **Position**: Middle-left

### 4. Default Rate by Education
- **Type**: Clustered Bar Chart
- **Title**: Default Rate by Education
- **Axis**: `DimEducation[education_label]`
- **Values**: `Overall Default Rate`
- **Sorting**: Descending by Value
- **Position**: Middle-center

### 5. Defaulters by Credit Limit Group
- **Type**: Stacked Column Chart
- **Title**: Defaulters by Credit Limit Group
- **Axis**: `DimCreditLimitGroup[credit_limit_group]`
- **Legend**: `DimDefaultStatus[default_label]`
- **Values**: `Total Customers`
- **Position**: Middle-right

### 6. Portfolio Risk Summary
- **Type**: Matrix / Table
- **Title**: Portfolio Risk Summary
- **Rows**: `DimCreditLimitGroup[credit_limit_group]`
- **Values**: `Total Customers`, `Total Defaulters`, `Overall Default Rate`
- **Conditional Formatting**: Background color on `Overall Default Rate` (Red-Orange-Green scale)
- **Position**: Bottom, full width
