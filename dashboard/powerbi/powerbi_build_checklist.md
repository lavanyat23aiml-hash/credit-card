# Power BI Build Checklist

Follow this checklist precisely when manually building the `.pbix` file.

- [ ] **1. Data Import:** Load all 11 CSV files from `data/processed/powerbi/`.
- [ ] **2. Data Types:** Verify numeric columns (Limit, Age, Ratios) are `Whole Number` or `Decimal Number`.
- [ ] **3. Row Counts:** Confirm `FactCreditCustomer` has exactly 30,000 rows.
- [ ] **4. Model Relationships:** 
  - Ensure all relationships are manually mapped (Dimension -> Fact).
  - Check cardinality is `1:Many`.
  - Check cross-filter is `Single`.
- [ ] **5. DAX Measures:** Copy and paste all DAX from `dax_measures.txt` into a dedicated `_Measures` table.
- [ ] **6. Theming:** Apply custom theme hex codes (Navy, Red, Green, Orange) via View > Customize Theme.
- [ ] **7. Build Pages:** Construct the 5 pages following `dashboard_wireframe.md`.
- [ ] **8. Formatting:** Hide empty visuals, ensure titles are left-aligned and sized consistently (e.g., 14pt Segoe UI).
- [ ] **9. Slicers:** Convert list slicers to dropdowns to save space where appropriate.
- [ ] **10. Tooltips:** Verify hovering over bars shows raw counts and measures correctly.
- [ ] **11. Drill-Through:** Configure Page 5 to accept drill-through filters from `AgeGroup`, `CreditLimitGroup`, and `Education`.
- [ ] **12. Conditional Formatting:** Apply background color conditional formatting to the Page 5 table (Red if Default = 1).
- [ ] **13. Validation:** Spot-check that Overall Default Rate is ~22.1%.
- [ ] **14. Save:** Save the file as `CreditGuard_Dashboard.pbix`.
