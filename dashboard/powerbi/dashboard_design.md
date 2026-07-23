# CreditGuard Power BI Dashboard Design

## Objective
To provide a professional executive-level Power BI dashboard that helps credit-risk analysts and financial decision-makers understand portfolio risk, customer segments, repayment behaviour, financial patterns, and the performance of the CreditGuard machine learning models.

## Target Users
- Credit-Risk Analysts
- Financial Business Analysts
- Risk-Management Teams

## Source Files
Located in `data/processed/powerbi/`:
- `FactCreditCustomer.csv`
- `DimAgeGroup.csv`
- `DimCreditLimitGroup.csv`
- `DimEducation.csv`
- `DimMarriage.csv`
- `DimSex.csv`
- `DimDefaultStatus.csv`
- `DimRepaymentStatus.csv`
- `ModelPerformance.csv`
- `ThresholdAnalysis.csv`
- `FeatureImportance.csv`

## Data Model (Star Schema)
This is a standard Star Schema optimized for Power BI.
**Fact Table**: `FactCreditCustomer` (30,000 unique rows, grain: 1 row per customer)
**Dimension Tables**:
- `DimAgeGroup` (surrogate or string key maps to `age_group` in Fact)
- `DimCreditLimitGroup`
- `DimEducation`
- `DimMarriage`
- `DimSex`
- `DimDefaultStatus`
- `DimRepaymentStatus`

### Relationships
- **Cardinality**: `1:N` (One to Many). Dimension tables are strictly on the `One` side. FactCreditCustomer is strictly on the `Many` side.
- **Direction**: Single-direction filtering from Dimension -> Fact. 
- **Rule**: Do not enable automatic bidirectional filtering to avoid ambiguous filter contexts.

## Recommended Page Size
- Standard 16:9 (1280 x 720 pixels).

## Navigation Design
- Left-rail collapsed navigation menu (using shape/buttons) or a top-rail tab design.
- Include a "Reset Filters" bookmark button on each page.

## Page Layout & Configuration

### Page 1 — Executive Overview
- **Visual Titles**: "Portfolio Risk Summary", "Default Rate by Segment"
- **Filters/Slicers**: Top right slicer pane for standard demographics (Age, Sex, Education).
- **Tooltips**: Use basic tooltips showing total customer count when hovering over percentage bars.

### Page 2 — Customer Segmentation
- **Visual Titles**: "High-Risk Customer Segments", "Defaulter Count vs Rate"
- **Filters/Slicers**: Dedicated side panel for segmentation drill-down.
- **Drill-through**: Allow users to right-click a segment (e.g., "University Educated, High Limit") and drill through to Page 5 (High-Risk Explorer).

### Page 3 — Repayment and Financial Behaviour
- **Visual Titles**: "Credit Utilisation by Risk", "Payment-to-Bill Ratio Over Time"
- **Filters/Slicers**: Default Status slicer.

### Page 4 — Model Performance
- **Visual Titles**: "Feature Importance Overview", "Threshold Optimization Trade-offs"
- **Filters/Slicers**: Model Name slicer.

### Page 5 — High-Risk Customer Explorer
- **Visual Titles**: "Detailed Customer Risk Log"
- **Filters/Slicers**: Delay Count, Maximum Delay, Default Status, Utilisation bracket.
- **Conditional Formatting**: Highlight rows in Red where `default_payment_next_month = 1`.

## Accessibility Recommendations
- Ensure high contrast for text (e.g., Dark Navy on white).
- Use distinct pattern fills if colors are close, ensuring red/green color-blind users can differentiate "High Risk" from "Safe".
- Include descriptive Alt-Text on the primary KPI cards and charts.
