import sqlite3
import pandas as pd
import os
import sys

def setup_database():
    csv_path = 'data/processed/creditguard_cleaned.csv'
    db_path = 'data/processed/creditguard.db'
    
    # 1. Validate dataset existence
    if not os.path.exists(csv_path):
        print(f"[ERROR] Cleaned dataset not found at {csv_path}.")
        print("Please ensure Phase 3 (Data Cleaning) was completed successfully.")
        sys.exit(1)
        
    print(f"[INFO] Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # 2. Connect to SQLite (creates file if it doesn't exist)
    print(f"[INFO] Connecting to SQLite database at {db_path}...")
    conn = sqlite3.connect(db_path)
    
    try:
        # 3. Create or replace table and insert all records
        print("[INFO] Creating table 'credit_customers' and inserting records...")
        df.to_sql('credit_customers', conn, if_exists='replace', index=False)
        
        # 4. Verify record count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM credit_customers;")
        count = cursor.fetchone()[0]
        
        if count == 30000:
            print(f"[SUCCESS] Successfully inserted {count} records into 'credit_customers'.")
        else:
            print(f"[WARNING] Inserted {count} records, but expected 30000.")
            
        # 5. Print table schema for verification
        print("\n--- Table Schema (credit_customers) ---")
        cursor.execute("PRAGMA table_info(credit_customers);")
        columns = cursor.fetchall()
        for col in columns:
            # col layout: (cid, name, type, notnull, dflt_value, pk)
            print(f" - {col[1]} ({col[2]})")
            
        print("\n[SUCCESS] Database setup completed successfully.")
        
    except Exception as e:
        print(f"[ERROR] An error occurred during database setup: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()
