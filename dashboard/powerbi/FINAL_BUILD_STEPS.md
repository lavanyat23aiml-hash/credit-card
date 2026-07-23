# CreditGuard Power BI Dashboard Final Build Steps

This guide is a strict, beginner-friendly sequence to construct the CreditGuard dashboard locally using Power BI Desktop. Because automated generation of `.pbix` files via Python is unsupported and prone to corruption, we have provided all safe, copy-pasteable assets to ensure a flawless manual build.

## Prerequisites
Ensure all required files are located in `data/processed/powerbi/`.
Ensure you know the absolute path to this folder (e.g., `C:\Your\Path\To\creditguard-credit-risk\data\processed\powerbi`).

## Exact Build Sequence

1. **Open Power BI Desktop**: Start a new blank report.
2. **Disable Automatic Relationship Detection**:
   - Go to `File` -> `Options and settings` -> `Options`.
   - Under `Current File` -> `Data Load`, untick "Autodetect new relationships after data is loaded".
3. **Create the ProjectDataFolder Parameter**:
   - Click `Transform data` to open the Power Query Editor.
   - Click `Manage Parameters` -> `New Parameter`.
   - Name it exactly: `ProjectDataFolder`
   - Type: `Text`
   - Current Value: Paste the absolute path to your `data/processed/powerbi` folder (do NOT include a trailing slash).
4. **Paste Power Query M Scripts**:
   - In Power Query Editor, right-click the queries pane -> `New Query` -> `Blank Query`.
   - Click `Advanced Editor`.
   - Paste the contents of `dashboard/powerbi/power_query/FactCreditCustomer.m` and name the query `FactCreditCustomer`.
   - Repeat this exact process for the other 5 scripts (`BillAmountMonthly.m`, `PayAmountMonthly.m`, `RepaymentHistoryUnpivoted.m`, `DimAgeGroup.m`, `DimCreditLimitGroup.m`).
5. **Load the Remaining CSV Tables**:
   - Use `New Source` -> `Text/CSV` to load `DimEducation.csv`, `DimSex.csv`, `DimMarriage.csv`, `DimDefaultStatus.csv`, `DimRepaymentStatus.csv`, `ModelPerformance.csv`, `ThresholdAnalysis.csv`, and `FeatureImportance.csv`.
   - Click `Close & Apply` to load all data into the model.
6. **Import the Theme JSON**:
   - Go to `View` -> `Themes` dropdown -> `Browse for themes`.
   - Select `dashboard/powerbi/creditguard_theme.json`.
7. **Verify Data Types and Row Counts**:
   - Go to Data view and verify `FactCreditCustomer` has exactly 30,000 rows.
   - Ensure `id` is set to "Don't summarize" (Model view -> Properties -> Summarize by -> None).
8. **Create Relationships**:
   - Go to Model view.
   - Using `dashboard/powerbi/model_relationships.csv` as your exact guide, drag and drop columns to create the 9 required 1:* single-direction relationships.
   - **Crucial**: Ensure `ModelPerformance`, `ThresholdAnalysis`, and `FeatureImportance` remain completely disconnected.
9. **Create the Measures Table**:
   - Click `Enter Data` from the Home ribbon. Name the table `_Measures`. Click Load.
10. **Paste DAX Measures**:
    - Open `dashboard/powerbi/dax_measures.txt`.
    - Right-click `_Measures` and select `New Measure` for all 26 equations.
11. **Configure Sort-By Columns**:
    - Select `DimAgeGroup[age_group]` in the Data pane, go to `Column tools` -> `Sort by column`, and choose `Age Group Sort`.
    - Repeat for `DimCreditLimitGroup` using `Credit Limit Group Sort`.
12. **Build Pages 1–5**:
    - Using the exact specifications in `dashboard/powerbi/pages/01` through `05`, add visuals, axes, and measures.
13. **Build the Hidden Drill-through Page**:
    - Follow `dashboard/powerbi/pages/06_customer_detail_drillthrough.md`.
    - Set the page to Hidden, and drag `FactCreditCustomer[id]` to the Drill-through field well.
14. **Configure Slicers, Tooltips, and Interactions**:
    - Ensure Page 1 slicers are synced via `View` -> `Sync slicers`.
    - Test the drill-through by right-clicking a row on Page 5.
15. **Validate Totals**:
    - Drop `Overall Default Rate` on a blank card. It should read approximately 22.1%.
16. **Save**:
    - Save the completed file as `CreditGuard_Dashboard.pbix` in the root folder.
