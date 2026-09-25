import os
import sys
import time
import subprocess
import psycopg2
from dotenv import load_dotenv

# Set up paths for importing local modules
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.ingestion import load_staging
from src.validation import dq_checks
from src.cleaning import clean_data
from src.analytics import create_views
from src.reporting import create_excel_report

def run_step(step_name, module):
    print(f"\n{'='*50}")
    print(f"STARTING: {step_name}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    try:
        module.main()
    except SystemExit as e:
        if e.code != 0:
            print(f"ERROR: {step_name} failed with exit code {e.code}.")
            sys.exit(e.code)
    except Exception as e:
        print(f"ERROR: {step_name} encountered an unexpected error: {e}")
        sys.exit(1)
        
    elapsed = time.time() - start_time
    print(f"COMPLETED: {step_name} in {elapsed:.2f} seconds.")

def validate_baselines():
    print(f"\n{'='*50}")
    print(f"STARTING: Final Baseline Validation")
    print(f"{'='*50}")
    
    load_dotenv()
    try:
        conn = psycopg2.connect(
            dbname="automated_business_reporting",
            user=os.environ.get("PG_USER"),
            password=os.environ.get("PG_PASSWORD"),
            host=os.environ.get("PG_HOST"),
            port=os.environ.get("PG_PORT")
        )
        cursor = conn.cursor()
    except Exception as e:
        print(f"ERROR: Failed to connect to database for validation: {e}")
        sys.exit(1)

    baselines = {
        "Orders": {"query": "SELECT total_orders FROM analytics.v_order_kpis;", "expected": 99441},
        "Customers": {"query": "SELECT total_customers FROM analytics.v_order_kpis;", "expected": 96096},
        "Repeat customers": {"query": "SELECT repeat_customers FROM analytics.v_order_kpis;", "expected": 2997},
        "GMV": {"query": "SELECT gmv FROM analytics.v_order_kpis;", "expected": 13591643.70},
        "Freight": {"query": "SELECT total_freight FROM analytics.v_order_kpis;", "expected": 2251909.54},
        "Merchandise + Freight": {"query": "SELECT merchandise_plus_freight FROM analytics.v_order_kpis;", "expected": 15843553.24},
        "Items sold": {"query": "SELECT total_items FROM analytics.v_order_kpis;", "expected": 112650},
        "Average Review Score": {"query": "SELECT average_review_score FROM analytics.v_order_kpis;", "expected": 4.09},
        "Payment Value": {"query": "SELECT SUM(total_payment_value) FROM analytics.v_payment_analysis;", "expected": 16008683.49},
        "Timestamp anomalies": {"query": "SELECT orders_with_timestamp_anomalies FROM analytics.v_data_quality_summary;", "expected": 1382},
        "Missing product categories": {"query": "SELECT products_with_missing_category FROM analytics.v_data_quality_summary;", "expected": 610},
        "Invalid payment records": {"query": "SELECT invalid_payment_records FROM analytics.v_data_quality_summary;", "expected": 2},
        "Invalid product records": {"query": "SELECT invalid_product_records FROM analytics.v_data_quality_summary;", "expected": 6},
        "Total invalid records": {"query": "SELECT total_invalid_records FROM analytics.v_data_quality_summary;", "expected": 8},
    }

    all_passed = True
    
    for name, data in baselines.items():
        cursor.execute(data["query"])
        result = cursor.fetchone()[0]
        
        # Convert numeric results to float for comparison if expected is float
        if isinstance(data["expected"], float):
            result_float = float(result) if result is not None else 0.0
            match = abs(result_float - data["expected"]) < 0.01
            result_display = f"{result_float:.2f}"
            expected_display = f"{data['expected']:.2f}"
        else:
            match = (result == data["expected"])
            result_display = str(result)
            expected_display = str(data["expected"])
            
        status = "PASS" if match else "FAIL"
        if not match:
            all_passed = False
            
        print(f"[{status}] {name.ljust(30)} | Expected: {expected_display.ljust(15)} | Actual: {result_display}")

    cursor.close()
    conn.close()

    if all_passed:
        print("\nAll baseline validations passed successfully!")
    else:
        print("\nFinal validation failed. Some metrics did not match the expected baselines.")
        sys.exit(1)

def main():
    print("starting Automated Business Reporting Pipeline...")
    total_start_time = time.time()
    
    # Run the pipeline steps in sequence
    run_step("1. Ingestion (Load Staging)", load_staging)
    run_step("2. Validation (Data Quality Checks)", dq_checks)
    run_step("3. Cleaning & Transformation", clean_data)
    run_step("4. Analytics (Create Views)", create_views)
    run_step("5. Reporting (Create Excel Report)", create_excel_report)
    
    # Run final validation
    validate_baselines()
    
    total_elapsed = time.time() - total_start_time
    print(f"\n{'='*50}")
    print(f"PIPELINE COMPLETED SUCCESSFULLY in {total_elapsed:.2f} seconds.")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
