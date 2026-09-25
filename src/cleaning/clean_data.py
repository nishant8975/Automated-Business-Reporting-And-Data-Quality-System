import os
import psycopg2
from dotenv import load_dotenv
import pandas as pd

def get_conn():
    load_dotenv()
    return psycopg2.connect(
        dbname="automated_business_reporting",
        user=os.environ.get("PG_USER"),
        password=os.environ.get("PG_PASSWORD"),
        host=os.environ.get("PG_HOST"),
        port=os.environ.get("PG_PORT")
    )

def main():
    conn = get_conn()
    conn.autocommit = True
    cursor = conn.cursor()
    
    # 1. SETUP INVALID RECORDS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality.invalid_records (
            invalid_record_id SERIAL PRIMARY KEY,
            source_table TEXT,
            record_identifier TEXT,
            rule_id TEXT,
            rule_name TEXT,
            failure_reason TEXT,
            original_values_or_context JSONB,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        TRUNCATE TABLE quality.invalid_records;
    """)

    # 2. CUSTOMERS
    cursor.execute("DROP TABLE IF EXISTS clean.customers CASCADE;")
    cursor.execute("""
        CREATE TABLE clean.customers AS
        SELECT 
            customer_id::TEXT,
            customer_unique_id::TEXT,
            customer_zip_code_prefix::TEXT,
            customer_city::TEXT,
            customer_state::TEXT
        FROM staging.customers;
    """)
    
    # 3. SELLERS
    cursor.execute("DROP TABLE IF EXISTS clean.sellers CASCADE;")
    cursor.execute("""
        CREATE TABLE clean.sellers AS
        SELECT 
            seller_id::TEXT,
            seller_zip_code_prefix::TEXT,
            seller_city::TEXT,
            seller_state::TEXT
        FROM staging.sellers;
    """)
    
    # 4. TRANSLATION
    cursor.execute("DROP TABLE IF EXISTS clean.product_category_name_translation CASCADE;")
    cursor.execute("""
        CREATE TABLE clean.product_category_name_translation AS
        SELECT 
            product_category_name::TEXT,
            product_category_name_english::TEXT
        FROM staging.product_category_name_translation;
    """)
    
    # 5. PRODUCTS (Quarantine invalid dims, but insert ID to clean)
    # Insert quarantine records
    cursor.execute("""
        INSERT INTO quality.invalid_records (source_table, record_identifier, rule_id, rule_name, failure_reason, original_values_or_context)
        SELECT 
            'products',
            product_id,
            CASE WHEN CAST(product_weight_g AS NUMERIC) <= 0 THEN 'DOM-products-weight' ELSE 'COMP-products-dims' END,
            'Physical Dimensions Validation',
            CASE WHEN CAST(product_weight_g AS NUMERIC) <= 0 THEN 'Weight must be > 0' ELSE 'Missing all physical dimensions' END,
            row_to_json(t)
        FROM staging.products t
        WHERE product_weight_g IS NULL
           OR product_length_cm IS NULL
           OR product_height_cm IS NULL
           OR product_width_cm IS NULL
           OR CAST(product_weight_g AS NUMERIC) <= 0;
    """)
    
    # Create clean products
    cursor.execute("DROP TABLE IF EXISTS clean.products CASCADE;")
    cursor.execute("""
        CREATE TABLE clean.products AS
        SELECT 
            product_id::TEXT,
            product_category_name::TEXT,
            product_name_lenght::NUMERIC,
            product_description_lenght::NUMERIC,
            product_photos_qty::NUMERIC,
            -- NULL out invalid dimensions
            CASE WHEN product_weight_g IS NULL OR CAST(product_weight_g AS NUMERIC) <= 0 THEN NULL ELSE CAST(product_weight_g AS NUMERIC) END AS product_weight_g,
            CASE WHEN product_weight_g IS NULL OR CAST(product_weight_g AS NUMERIC) <= 0 THEN NULL ELSE CAST(product_length_cm AS NUMERIC) END AS product_length_cm,
            CASE WHEN product_weight_g IS NULL OR CAST(product_weight_g AS NUMERIC) <= 0 THEN NULL ELSE CAST(product_height_cm AS NUMERIC) END AS product_height_cm,
            CASE WHEN product_weight_g IS NULL OR CAST(product_weight_g AS NUMERIC) <= 0 THEN NULL ELSE CAST(product_width_cm AS NUMERIC) END AS product_width_cm
        FROM staging.products;
    """)

    # 6. ORDERS (Timestamps handling)
    cursor.execute("DROP TABLE IF EXISTS clean.orders CASCADE;")
    cursor.execute("""
        CREATE TABLE clean.orders AS
        SELECT 
            order_id::TEXT,
            customer_id::TEXT,
            order_status::TEXT,
            CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
            
            -- Validation logic for approved_at (Must be >= purchase)
            CASE WHEN order_approved_at IS NOT NULL AND CAST(order_approved_at AS TIMESTAMP) < CAST(order_purchase_timestamp AS TIMESTAMP) THEN FALSE 
                 WHEN order_approved_at IS NULL THEN NULL ELSE TRUE END AS is_order_approved_at_valid,
            CASE WHEN order_approved_at IS NOT NULL AND CAST(order_approved_at AS TIMESTAMP) < CAST(order_purchase_timestamp AS TIMESTAMP) THEN NULL 
                 ELSE CAST(order_approved_at AS TIMESTAMP) END AS order_approved_at,
            
            -- Validation logic for carrier (Must be >= approved_at) (Violation A)
            CASE WHEN order_delivered_carrier_date IS NOT NULL AND order_approved_at IS NOT NULL AND CAST(order_delivered_carrier_date AS TIMESTAMP) < CAST(order_approved_at AS TIMESTAMP) THEN FALSE 
                 WHEN order_delivered_carrier_date IS NULL THEN NULL ELSE TRUE END AS is_order_delivered_carrier_date_valid,
            CASE WHEN order_delivered_carrier_date IS NOT NULL AND order_approved_at IS NOT NULL AND CAST(order_delivered_carrier_date AS TIMESTAMP) < CAST(order_approved_at AS TIMESTAMP) THEN NULL 
                 ELSE CAST(order_delivered_carrier_date AS TIMESTAMP) END AS order_delivered_carrier_date,
            
            -- Validation logic for customer (Must be >= carrier) (Violation B)
            CASE WHEN order_delivered_customer_date IS NOT NULL AND order_delivered_carrier_date IS NOT NULL AND CAST(order_delivered_customer_date AS TIMESTAMP) < CAST(order_delivered_carrier_date AS TIMESTAMP) THEN FALSE 
                 WHEN order_delivered_customer_date IS NULL THEN NULL ELSE TRUE END AS is_order_delivered_customer_date_valid,
            CASE WHEN order_delivered_customer_date IS NOT NULL AND order_delivered_carrier_date IS NOT NULL AND CAST(order_delivered_customer_date AS TIMESTAMP) < CAST(order_delivered_carrier_date AS TIMESTAMP) THEN NULL 
                 ELSE CAST(order_delivered_customer_date AS TIMESTAMP) END AS order_delivered_customer_date,
            
            CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date
        FROM staging.orders;
    """)
    
    # 7. ORDER ITEMS
    cursor.execute("DROP TABLE IF EXISTS clean.order_items CASCADE;")
    cursor.execute("""
        CREATE TABLE clean.order_items AS
        SELECT 
            order_id::TEXT,
            order_item_id::INT,
            product_id::TEXT,
            seller_id::TEXT,
            CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,
            CAST(price AS NUMERIC) AS price,
            CAST(freight_value AS NUMERIC) AS freight_value
        FROM staging.order_items;
    """)
    
    # 8. ORDER PAYMENTS
    cursor.execute("""
        INSERT INTO quality.invalid_records (source_table, record_identifier, rule_id, rule_name, failure_reason, original_values_or_context)
        SELECT 
            'order_payments',
            order_id || '-' || payment_sequential,
            'DOM-order_payments-installments',
            'Installments > 0',
            'Installments is < 1',
            row_to_json(t)
        FROM staging.order_payments t
        WHERE CAST(payment_installments AS NUMERIC) < 1;
    """)
    
    cursor.execute("DROP TABLE IF EXISTS clean.order_payments CASCADE;")
    cursor.execute("""
        CREATE TABLE clean.order_payments AS
        SELECT 
            order_id::TEXT,
            payment_sequential::INT,
            payment_type::TEXT,
            CAST(payment_installments AS INT) AS payment_installments,
            CAST(payment_value AS NUMERIC) AS payment_value
        FROM staging.order_payments
        WHERE CAST(payment_installments AS NUMERIC) >= 1;
    """)
    
    # 9. ORDER REVIEWS
    cursor.execute("DROP TABLE IF EXISTS clean.order_reviews CASCADE;")
    cursor.execute("""
        CREATE TABLE clean.order_reviews AS
        SELECT 
            review_id::TEXT,
            order_id::TEXT,
            CAST(review_score AS INT) AS review_score,
            review_comment_title::TEXT,
            review_comment_message::TEXT,
            CAST(review_creation_date AS TIMESTAMP) AS review_creation_date,
            CAST(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp
        FROM staging.order_reviews;
    """)
    
    print("CLEANING COMPLETE.")
    
    # KPIs before/after
    def get_cnt(query):
        cursor.execute(query)
        return cursor.fetchone()[0]
        
    print("\n--- ROW COUNTS BEFORE / AFTER ---")
    print(f"customers:      Staging: {get_cnt('SELECT COUNT(*) FROM staging.customers')} | Clean: {get_cnt('SELECT COUNT(*) FROM clean.customers')}")
    print(f"orders:         Staging: {get_cnt('SELECT COUNT(*) FROM staging.orders')} | Clean: {get_cnt('SELECT COUNT(*) FROM clean.orders')}")
    print(f"order_items:    Staging: {get_cnt('SELECT COUNT(*) FROM staging.order_items')} | Clean: {get_cnt('SELECT COUNT(*) FROM clean.order_items')}")
    print(f"order_payments: Staging: {get_cnt('SELECT COUNT(*) FROM staging.order_payments')} | Clean: {get_cnt('SELECT COUNT(*) FROM clean.order_payments')}")
    print(f"order_reviews:  Staging: {get_cnt('SELECT COUNT(*) FROM staging.order_reviews')} | Clean: {get_cnt('SELECT COUNT(*) FROM clean.order_reviews')}")
    print(f"products:       Staging: {get_cnt('SELECT COUNT(*) FROM staging.products')} | Clean: {get_cnt('SELECT COUNT(*) FROM clean.products')}")
    
    print("\n--- QUARANTINED ---")
    cursor.execute("SELECT source_table, COUNT(*) FROM quality.invalid_records GROUP BY source_table;")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} records quarantined.")
        
    print("\n--- TIMESTAMPS NULLIFIED ---")
    print(f"Approved At invalid (carrier < approved): {get_cnt('SELECT COUNT(*) FROM clean.orders WHERE is_order_delivered_carrier_date_valid = FALSE')}")
    print(f"Customer Date invalid (customer < carrier): {get_cnt('SELECT COUNT(*) FROM clean.orders WHERE is_order_delivered_customer_date_valid = FALSE')}")
    
    print("\n--- BUSINESS VOLUME RECONCILIATION ---")
    print(f"Staging Total Items Price: {get_cnt('SELECT SUM(CAST(price AS NUMERIC)) FROM staging.order_items')}")
    print(f"Clean Total Items Price:   {get_cnt('SELECT SUM(price) FROM clean.order_items')}")
    print(f"Staging Total Freight:     {get_cnt('SELECT SUM(CAST(freight_value AS NUMERIC)) FROM staging.order_items')}")
    print(f"Clean Total Freight:       {get_cnt('SELECT SUM(freight_value) FROM clean.order_items')}")
    print(f"Staging Total Payments:    {get_cnt('SELECT SUM(CAST(payment_value AS NUMERIC)) FROM staging.order_payments')}")
    print(f"Clean Total Payments:      {get_cnt('SELECT SUM(payment_value) FROM clean.order_payments')}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
