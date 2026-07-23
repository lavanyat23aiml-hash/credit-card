# Power Query Steps & Data Import Guidance

Follow these steps exactly in Power BI Desktop to load the data cleanly and avoid automatic relationship errors.

## 1. Import Data
1. Open Power BI Desktop.
2. Go to **Get Data** > **Text/CSV**.
3. Navigate to `data/processed/powerbi/`.
4. Import `FactCreditCustomer.csv`. Click **Transform Data** (do NOT click Load yet).
5. Repeat **New Source** > **Text/CSV** for all remaining CSV files in the folder (Dimensions, Model Performance, Threshold Analysis, Feature Importance).

## 2. Power Query Transformations
In the Power Query Editor, verify the following for every table:
- **Promote Headers**: Ensure the first row was correctly promoted to headers (`Use First Row as Headers`).
- **Data Types**:
  - `FactCreditCustomer`: 
    - `id`, `age`, `delayed_payment_count`, `maximum_delay_months` -> **Whole Number**
    - `limit_bal`, `average_bill_amount`, `average_payment_amount`, `payment_to_bill_ratio`, `credit_utilisation_ratio` -> **Decimal Number**
    - `default_payment_next_month`, `has_payment_delay` -> **Whole Number**
- **Trimming**: Select all text columns (e.g., labels in Dim tables), right-click -> **Transform** -> **Trim** to remove trailing whitespace.
- **Replacing Errors**: Ensure no `NaN` or `Error` values exist. If found, right-click the column header -> **Replace Errors** (use 0 or null depending on context).

## 3. Verify Row Counts
- Click on `FactCreditCustomer`. Look at the bottom left status bar in Power Query. It must say exactly **30,000 rows**. If it says "999+ rows", you can click `Count Rows` in the Transform ribbon to verify. It must be exactly 30,000.

## 4. Relationship Creation (Crucial)
1. Close & Apply to load data into the model.
2. Go to the **Model View** (third icon on the left).
3. **Turn OFF Automatic Relationships**: Go to File > Options and settings > Options > Current File > Data Load. Uncheck "Autodetect new relationships after data is loaded".
4. Delete any incorrect relationships Power BI guessed automatically.
5. Create relationships manually by dragging:
   - `DimAgeGroup[age_group]` -> `FactCreditCustomer[age_group]`
   - `DimCreditLimitGroup[credit_limit_group]` -> `FactCreditCustomer[credit_limit_group]`
   - `DimEducation[education]` -> `FactCreditCustomer[education]`
   - `DimMarriage[marriage]` -> `FactCreditCustomer[marriage]`
   - `DimSex[sex]` -> `FactCreditCustomer[sex]`
   - `DimDefaultStatus[default_payment_next_month]` -> `FactCreditCustomer[default_payment_next_month]`
6. Select each relationship line, look at properties pane:
   - Cardinality: **1 to Many** (Dimension is 1, Fact is *).
   - Cross filter direction: **Single**.

## 5. Final Checks
- Do not link `ModelPerformance` or `FeatureImportance` to the Fact table. They are isolated tables purely for Page 4 visuals.
