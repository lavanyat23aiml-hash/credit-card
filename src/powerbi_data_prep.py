import os
import pandas as pd
import sys

def create_directory_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def generate_powerbi_data():
    input_file = "data/processed/creditguard_cleaned.csv"
    output_dir = "data/processed/powerbi/"
    
    print("[INFO] Starting Power BI Data Preparation...")
    
    if not os.path.exists(input_file):
        print(f"[ERROR] Required input file not found: {input_file}")
        sys.exit(1)
        
    create_directory_if_not_exists(output_dir)
    
    # Read the master dataset
    df = pd.read_csv(input_file)
    print(f"[INFO] Loaded main dataset. Shape: {df.shape}")
    
    # Verify exact row count
    if len(df) != 30000:
        print(f"[ERROR] Fact table row count is {len(df)}, expected exactly 30,000.")
        sys.exit(1)
        
    # Generate Dimension Tables (must be unique)
    print("[INFO] Generating Dimension Tables...")
    
    # 1. DimAgeGroup
    dim_age = df[['age_group']].drop_duplicates().reset_index(drop=True)
    dim_age.to_csv(os.path.join(output_dir, "DimAgeGroup.csv"), index=False)
    
    # 2. DimCreditLimitGroup
    dim_limit = df[['credit_limit_group']].drop_duplicates().reset_index(drop=True)
    dim_limit.to_csv(os.path.join(output_dir, "DimCreditLimitGroup.csv"), index=False)
    
    # 3. DimSex
    dim_sex = df[['sex', 'sex_label']].drop_duplicates().reset_index(drop=True)
    dim_sex.to_csv(os.path.join(output_dir, "DimSex.csv"), index=False)
    
    # 4. DimEducation
    dim_edu = df[['education', 'education_label']].drop_duplicates().reset_index(drop=True)
    dim_edu.to_csv(os.path.join(output_dir, "DimEducation.csv"), index=False)
    
    # 5. DimMarriage
    dim_mar = df[['marriage', 'marriage_label']].drop_duplicates().reset_index(drop=True)
    dim_mar.to_csv(os.path.join(output_dir, "DimMarriage.csv"), index=False)
    
    # 6. DimDefaultStatus
    dim_default = df[['default_payment_next_month']].drop_duplicates().reset_index(drop=True)
    dim_default['default_label'] = dim_default['default_payment_next_month'].map({1: 'Defaulter', 0: 'Reliable'})
    dim_default.to_csv(os.path.join(output_dir, "DimDefaultStatus.csv"), index=False)
    
    # 7. DimRepaymentStatus (Just a lookup for values like -2 to 8, we infer from all pay_X columns)
    pay_values = pd.concat([df[f'pay_{i}'] for i in [0, 2, 3, 4, 5, 6]]).unique()
    dim_rep = pd.DataFrame({'repayment_status': sorted(pay_values)})
    dim_rep.to_csv(os.path.join(output_dir, "DimRepaymentStatus.csv"), index=False)
    
    # Generate Fact Table
    print("[INFO] Generating Fact Table...")
    # Select columns needed for the fact table (excluding labels already in dimensions, though we can keep age_group, credit_limit_group as text keys)
    fact_cols = [
        'id', 'limit_bal', 'age', 'age_group', 'credit_limit_group',
        'sex', 'education', 'marriage',
        'pay_0', 'pay_2', 'pay_3', 'pay_4', 'pay_5', 'pay_6',
        'bill_amt1', 'bill_amt2', 'bill_amt3', 'bill_amt4', 'bill_amt5', 'bill_amt6',
        'pay_amt1', 'pay_amt2', 'pay_amt3', 'pay_amt4', 'pay_amt5', 'pay_amt6',
        'average_bill_amount', 'average_payment_amount', 'total_bill_amount', 'total_payment_amount',
        'payment_to_bill_ratio', 'credit_utilisation_ratio', 
        'delayed_payment_count', 'maximum_delay_months', 'has_payment_delay',
        'default_payment_next_month'
    ]
    fact_df = df[fact_cols].copy()
    fact_df.to_csv(os.path.join(output_dir, "FactCreditCustomer.csv"), index=False)
    
    print("[INFO] Processing Model Reports...")
    model_files = {
        'model_comparison.csv': 'ModelPerformance.csv',
        'threshold_analysis.csv': 'ThresholdAnalysis.csv',
        'feature_importance.csv': 'FeatureImportance.csv'
    }
    
    for in_file, out_file in model_files.items():
        in_path = os.path.join('reports/model', in_file)
        out_path = os.path.join(output_dir, out_file)
        
        if os.path.exists(in_path):
            try:
                rep_df = pd.read_csv(in_path)
                rep_df.to_csv(out_path, index=False)
                print(f"[SUCCESS] Processed {out_file}.")
            except Exception as e:
                print(f"[ERROR] Failed to read {in_path}: {e}")
        else:
            # Create helpful validation error if missing
            print(f"[WARNING] Model report file '{in_path}' is missing.")
            print(f"          This file is required for the Power BI dashboard Page 4.")
            print(f"          Please ensure Phase 6 (Machine Learning) was completed.")
            # We create an empty structure so Power BI doesn't instantly break, but data won't exist.
            pd.DataFrame().to_csv(out_path, index=False)

    print(f"[SUCCESS] All Power BI data successfully prepared in {output_dir}")

if __name__ == "__main__":
    generate_powerbi_data()
