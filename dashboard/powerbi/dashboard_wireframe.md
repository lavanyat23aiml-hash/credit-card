# Power BI Dashboard Wireframes

## Page 1: Executive Overview
```text
[   Header: CreditGuard Executive Risk Overview                           ]
-------------------------------------------------------------------------
[ Total Cust: 30K ] [ Total Default: 6,636 ] [ Overall Default Rate: 22.1% ]
[ Avg Credit: 167K] [ Cust w/ Delay: XX ]    [ Avg Utilisation: XX% ]
-------------------------------------------------------------------------
|                                 |                                     |
| [Line/Bar] Default Rate by      | [Donut] Total Defaulters by         |
|            Age Group            |         Credit Limit Group          |
|                                 |                                     |
-------------------------------------------------------------------------
|                 |                               |                     |
| [Bar] Default   | [Bar] Default Rate by Sex     | [Text Box]          |
|  by Education   |                               | Portfolio Risk      |
|                 |                               | Summary             |
-------------------------------------------------------------------------
```

## Page 2: Customer Segmentation
```text
[   Header: Customer Segmentation & Risk Profile                        ]
-------------------------------------------------------------------------
| [Slicer Pane]   |                                                     |
| Age Group       | [Clustered Column] Default Rate by Demographics     |
| Limit Group     | (Age, Education, Marriage, Sex)                     |
| Education       |                                                     |
| Sex             |-----------------------------------------------------|
| Marriage        |                                                     |
|                 | [Matrix/Table] High-Risk Segment Breakdown          |
|                 | Columns: Segment, Size, Defaulter Count, Def. Rate  |
|                 | (Right-click drill-through enabled here)            |
-------------------------------------------------------------------------
```

## Page 3: Repayment and Financial Behaviour
```text
[   Header: Repayment Patterns & Financial Behaviour                    ]
-------------------------------------------------------------------------
| [Scatter Plot]                         | [Bar Chart]                  |
| Avg Bill vs Avg Payment                | Default Rate by              |
| Color: Default Status (Red/Green)      | Maximum Delay Months         |
|                                        |                              |
-------------------------------------------------------------------------
| [Line Chart]                           | [100% Stacked Bar]           |
| Monthly Bill vs Payment Trend          | Credit Utilisation           |
| (Over the 6-month period)              | by Default Status            |
-------------------------------------------------------------------------
```

## Page 4: Model Performance
```text
[   Header: ML Model Performance & Threshold Selection                  ]
-------------------------------------------------------------------------
[Slicer: Select Model (e.g., Random Forest Weighted)]
-------------------------------------------------------------------------
| [Table] Model Metrics          | [Line Chart] Threshold Trade-off     |
| Acc, Bal_Acc, Prec, Recall,    | False Positives vs False Negatives   |
| F1, ROC-AUC, Avg Precision     | over probability thresholds          |
-------------------------------------------------------------------------
| [Horizontal Bar Chart]         | [Card] Selected Threshold            |
| Top 10 Feature Importances     | [Card] Business Cost                 |
|                                | [Text] Model Selection Explanation   |
-------------------------------------------------------------------------
```

## Page 5: High-Risk Customer Explorer
```text
[   Header: High-Risk Customer Explorer (Drill-Through Target)          ]
-------------------------------------------------------------------------
| [Slicer] Delay Count    | [Slicer] Utilisation  | [Slicer] Default    |
-------------------------------------------------------------------------
| [Detailed Table]                                                      |
| ID | Age | Sex | Education | Limit | Delay Count | Utilisation | Def? |
|-----------------------------------------------------------------------|
| 1  | 25  | F   | Univ      | 50000 | 2           | 0.85        | 1    |
| 2  | 34  | M   | High Sch  | 10000 | 5           | 0.99        | 1    |
| (Rows with Def=1 highlighted via conditional formatting)              |
-------------------------------------------------------------------------
```
