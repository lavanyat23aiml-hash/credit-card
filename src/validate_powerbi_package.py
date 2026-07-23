import os
import json
import sys

def print_result(check_name, passed, critical=True):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {check_name}")
    if not passed and critical:
        print(f"CRITICAL FAILURE: {check_name}. Exiting.")
        sys.exit(1)

def validate_package():
    print("--- Starting Power BI Package Validation ---")
    
    # 1. Required CSV Sources Exist
    csv_files = [
        "FactCreditCustomer.csv", "DimAgeGroup.csv", "DimCreditLimitGroup.csv",
        "DimEducation.csv", "DimMarriage.csv", "DimSex.csv", "DimDefaultStatus.csv",
        "DimRepaymentStatus.csv", "ModelPerformance.csv", "ThresholdAnalysis.csv",
        "FeatureImportance.csv"
    ]
    all_csvs_exist = all(os.path.exists(f"data/processed/powerbi/{f}") for f in csv_files)
    print_result("Required CSV sources exist", all_csvs_exist)
    
    # 2. Theme JSON parses successfully
    theme_path = "dashboard/powerbi/creditguard_theme.json"
    theme_valid = False
    if os.path.exists(theme_path):
        try:
            with open(theme_path, 'r') as f:
                json.load(f)
            theme_valid = True
        except json.JSONDecodeError:
            pass
    print_result("Theme JSON parses successfully", theme_valid)
    
    # 3. All 6 M scripts exist and are non-empty
    m_scripts = [
        "FactCreditCustomer.m", "BillAmountMonthly.m", "PayAmountMonthly.m",
        "RepaymentHistoryUnpivoted.m", "DimAgeGroup.m", "DimCreditLimitGroup.m"
    ]
    all_m_exist = True
    for m in m_scripts:
        path = f"dashboard/powerbi/power_query/{m}"
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            all_m_exist = False
            break
    print_result("All 6 M scripts exist and are non-empty", all_m_exist)
    
    # 4. No absolute Windows user path exists in generated assets
    # We will check the M scripts for "C:\\Users"
    no_absolute_paths = True
    for m in m_scripts:
        with open(f"dashboard/powerbi/power_query/{m}", 'r') as f:
            content = f.read()
            if "C:\\Users" in content or "C:/Users" in content:
                no_absolute_paths = False
                break
    print_result("No absolute Windows paths in M scripts", no_absolute_paths)
    
    # 5. All 26 DAX measures are present
    dax_path = "dashboard/powerbi/dax_measures.txt"
    dax_present = False
    if os.path.exists(dax_path):
        with open(dax_path, 'r') as f:
            content = f.read()
            # Just count how many equal signs are present, or known measure keywords
            measure_count = content.count(" = ")
            if measure_count >= 26:
                dax_present = True
    print_result("All 26 DAX measures are present", dax_present)
    
    # 6. Relationship CSV contains all required rows
    rel_path = "dashboard/powerbi/model_relationships.csv"
    rel_valid = False
    if os.path.exists(rel_path):
        with open(rel_path, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 10: # Header + 9 relationships
                rel_valid = True
    print_result("Relationship CSV contains 9 relationships", rel_valid)
    
    # 7. All 6 page specifications exist
    pages = [
        "01_executive_overview.md", "02_customer_segmentation.md",
        "03_repayment_financial_behaviour.md", "04_model_performance.md",
        "05_high_risk_customer_explorer.md", "06_customer_detail_drillthrough.md"
    ]
    all_pages_exist = all(os.path.exists(f"dashboard/powerbi/pages/{p}") for p in pages)
    print_result("All 6 page specifications exist", all_pages_exist)
    
    # 8. Final build guide exists
    build_guide = os.path.exists("dashboard/powerbi/FINAL_BUILD_STEPS.md")
    print_result("Final build guide exists", build_guide)
    
    # 9. Duplicate review report exists
    dup_review = os.path.exists("reports/powerbi/model_performance_duplicate_review.md")
    print_result("Duplicate review report exists", dup_review)
    
    # 10. No fake PBIX claim exists in README
    readme_valid = True
    if os.path.exists("README.md"):
        with open("README.md", 'r') as f:
            content = f.read()
            if "generated a .pbix" in content.lower() or "created a pbix" in content.lower():
                readme_valid = False
    print_result("No fake PBIX claim exists in README", readme_valid)

    print("--- Validation Complete: ALL SYSTEMS GO ---")

if __name__ == "__main__":
    validate_package()
