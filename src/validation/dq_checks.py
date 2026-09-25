import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

def get_conn():
    load_dotenv()
    return psycopg2.connect(
        dbname="automated_business_reporting",
        user=os.environ.get("PG_USER"),
        password=os.environ.get("PG_PASSWORD"),
        host=os.environ.get("PG_HOST"),
        port=os.environ.get("PG_PORT")
    )

def setup_dq_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality.data_quality_results (
            run_id SERIAL PRIMARY KEY,
            rule_id TEXT,
            table_name TEXT,
            column_name TEXT,
            quality_dimension TEXT,
            severity TEXT,
            total_records BIGINT,
            failed_records BIGINT,
            failure_percentage NUMERIC,
            status TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        TRUNCATE TABLE quality.data_quality_results;
    """)

def run_check(cursor, rule_id, table_name, column_name, dimension, severity, total_query, fail_query):
    cursor.execute(total_query)
    total = cursor.fetchone()[0]
    
    cursor.execute(fail_query)
    failed = cursor.fetchone()[0]
    
    pct = (failed / total * 100) if total > 0 else 0
    
    status = 'PASS'
    if failed > 0:
        if severity == 'HIGH':
            status = 'FAIL'
        else:
            status = 'WARN'
            
    cursor.execute("""
        INSERT INTO quality.data_quality_results 
        (rule_id, table_name, column_name, quality_dimension, severity, total_records, failed_records, failure_percentage, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (rule_id, table_name, column_name, dimension, severity, total, failed, pct, status))
    
    return {'rule_id': rule_id, 'table': table_name, 'col': column_name, 'dim': dimension, 'total': total, 'failed': failed, 'pct': pct, 'status': status}

def generate_report(results):
    report = "# Data Quality Report\n\n## 1. Executive Summary\n"
    total_rules = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    warns = sum(1 for r in results if r['status'] == 'WARN')
    fails = sum(1 for r in results if r['status'] == 'FAIL')
    
    report += f"- Total Validation Rules: {total_rules}\n"
    report += f"- PASS: {passed}\n- WARN: {warns}\n- FAIL: {fails}\n\n"
    
    report += "## 2. Validation Results\n\n| Rule ID | Table | Column/Check | Dimension | Total | Failed | % | Status |\n|---|---|---|---|---|---|---|---|\n"
    for r in results:
        report += f"| {r['rule_id']} | {r['table']} | {r['col']} | {r['dim']} | {r['total']} | {r['failed']} | {r['pct']:.2f}% | {r['status']} |\n"
    
    report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
    os.makedirs(report_dir, exist_ok=True)
    with open(os.path.join(report_dir, "data_quality_report.md"), "w") as f:
        f.write(report)
    print("Report generated at reports/data_quality_report.md")

def main():
    conn = get_conn()
    conn.autocommit = True
    cursor = conn.cursor()
    
    setup_dq_table(cursor)
    results = []
    
    # --- COMPLETENESS ---
    comp_checks = [
        ('customers', 'customer_id'), ('customers', 'customer_unique_id'), ('customers', 'customer_zip_code_prefix'), ('customers', 'customer_city'), ('customers', 'customer_state'),
        ('orders', 'order_id'), ('orders', 'customer_id'), ('orders', 'order_status'), ('orders', 'order_purchase_timestamp'), ('orders', 'order_approved_at'), ('orders', 'order_delivered_carrier_date'), ('orders', 'order_delivered_customer_date'), ('orders', 'order_estimated_delivery_date'),
        ('order_items', 'order_id'), ('order_items', 'order_item_id'), ('order_items', 'product_id'), ('order_items', 'seller_id'), ('order_items', 'shipping_limit_date'), ('order_items', 'price'), ('order_items', 'freight_value'),
        ('order_payments', 'order_id'), ('order_payments', 'payment_sequential'), ('order_payments', 'payment_type'), ('order_payments', 'payment_installments'), ('order_payments', 'payment_value'),
        ('order_reviews', 'review_id'), ('order_reviews', 'order_id'), ('order_reviews', 'review_score'), ('order_reviews', 'review_creation_date'), ('order_reviews', 'review_answer_timestamp'), ('order_reviews', 'review_comment_title'), ('order_reviews', 'review_comment_message'),
        ('products', 'product_id'), ('products', 'product_category_name'), ('products', 'product_weight_g'), ('products', 'product_length_cm'), ('products', 'product_height_cm'), ('products', 'product_width_cm'),
        ('sellers', 'seller_id'), ('sellers', 'seller_zip_code_prefix'), ('sellers', 'seller_city'), ('sellers', 'seller_state')
    ]
    
    for table, col in comp_checks:
        severity = 'LOW' if col in ['order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date', 'review_comment_title', 'review_comment_message', 'product_category_name'] else 'HIGH'
        res = run_check(cursor, f"COMP-{table}-{col}", table, col, "COMPLETENESS", severity,
                  f"SELECT COUNT(*) FROM staging.{table}",
                  f"SELECT COUNT(*) FROM staging.{table} WHERE {col} IS NULL")
        results.append(res)
        
    # --- UNIQUENESS ---
    uniq_checks = [
        ('customers', 'customer_id', 'customer_id'),
        ('orders', 'order_id', 'order_id'),
        ('order_items', 'order_id, order_item_id', 'order_id, order_item_id'),
        ('order_payments', 'order_id, payment_sequential', 'order_id, payment_sequential'),
        ('order_reviews', 'review_id, order_id', 'review_id, order_id'),
        ('products', 'product_id', 'product_id'),
        ('sellers', 'seller_id', 'seller_id'),
        ('product_category_name_translation', 'product_category_name', 'product_category_name')
    ]
    
    for table, col, group_cols in uniq_checks:
        res = run_check(cursor, f"UNIQ-{table}", table, col, "UNIQUENESS", "HIGH",
                  f"SELECT COUNT(*) FROM staging.{table}",
                  f"SELECT COUNT(*) FROM (SELECT {group_cols}, COUNT(*) FROM staging.{table} GROUP BY {group_cols} HAVING COUNT(*) > 1) sq")
        results.append(res)
        
    # --- REFERENTIAL INTEGRITY ---
    ref_checks = [
        ('orders', 'customers', 'customer_id', 'customer_id'),
        ('order_items', 'orders', 'order_id', 'order_id'),
        ('order_items', 'products', 'product_id', 'product_id'),
        ('order_items', 'sellers', 'seller_id', 'seller_id'),
        ('order_payments', 'orders', 'order_id', 'order_id'),
        ('order_reviews', 'orders', 'order_id', 'order_id')
    ]
    
    for src, tgt, src_col, tgt_col in ref_checks:
        res = run_check(cursor, f"REF-{src}-{tgt}", src, src_col, "REFERENTIAL", "HIGH",
                  f"SELECT COUNT(*) FROM staging.{src}",
                  f"SELECT COUNT(*) FROM staging.{src} LEFT JOIN staging.{tgt} ON staging.{src}.{src_col} = staging.{tgt}.{tgt_col} WHERE staging.{tgt}.{tgt_col} IS NULL")
        results.append(res)
        
    # --- DOMAIN/NUMERIC ---
    num_checks = [
        ('order_items', 'price', 'CAST(price AS NUMERIC) < 0'),
        ('order_items', 'freight_value', 'CAST(freight_value AS NUMERIC) < 0'),
        ('order_payments', 'payment_value', 'CAST(payment_value AS NUMERIC) < 0'),
        ('order_payments', 'payment_installments', 'CAST(payment_installments AS NUMERIC) < 1'),
        ('order_payments', 'payment_sequential', 'CAST(payment_sequential AS NUMERIC) < 1'),
        ('order_reviews', 'review_score', 'CAST(review_score AS NUMERIC) < 1 OR CAST(review_score AS NUMERIC) > 5'),
        ('products', 'product_weight_g', 'CAST(product_weight_g AS NUMERIC) <= 0'),
        ('products', 'product_length_cm', 'CAST(product_length_cm AS NUMERIC) <= 0'),
        ('products', 'product_height_cm', 'CAST(product_height_cm AS NUMERIC) <= 0'),
        ('products', 'product_width_cm', 'CAST(product_width_cm AS NUMERIC) <= 0')
    ]
    
    for table, col, condition in num_checks:
        res = run_check(cursor, f"DOM-{table}-{col}", table, col, "VALIDITY", "HIGH",
                  f"SELECT COUNT(*) FROM staging.{table} WHERE {col} IS NOT NULL",
                  f"SELECT COUNT(*) FROM staging.{table} WHERE {col} IS NOT NULL AND ({condition})")
        results.append(res)
        
    # --- DATES ---
    date_checks = [
        ('orders', 'order_purchase_timestamp <= order_approved_at', 'CAST(order_purchase_timestamp AS TIMESTAMP) > CAST(order_approved_at AS TIMESTAMP)'),
        ('orders', 'order_approved_at <= order_delivered_carrier_date', 'CAST(order_approved_at AS TIMESTAMP) > CAST(order_delivered_carrier_date AS TIMESTAMP)'),
        ('orders', 'order_delivered_carrier_date <= order_delivered_customer_date', 'CAST(order_delivered_carrier_date AS TIMESTAMP) > CAST(order_delivered_customer_date AS TIMESTAMP)')
    ]
    
    for table, name, condition in date_checks:
        cols = condition.split('CAST(')[1].split(' AS')[0] # roughly extracting
        res = run_check(cursor, f"DATE-{name}", table, name, "CONSISTENCY", "HIGH",
                  f"SELECT COUNT(*) FROM staging.{table}",
                  f"SELECT COUNT(*) FROM staging.{table} WHERE order_purchase_timestamp IS NOT NULL AND order_approved_at IS NOT NULL AND order_delivered_carrier_date IS NOT NULL AND order_delivered_customer_date IS NOT NULL AND ({condition})")
        results.append(res)
        
    generate_report(results)
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
