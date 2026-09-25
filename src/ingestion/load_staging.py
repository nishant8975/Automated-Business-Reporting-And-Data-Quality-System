import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from dotenv import load_dotenv

def main():
    # Load .env
    load_dotenv()
    pg_host = os.environ.get("PG_HOST")
    pg_port = os.environ.get("PG_PORT")
    pg_user = os.environ.get("PG_USER")
    pg_password = os.environ.get("PG_PASSWORD")
    
    db_name = "automated_business_reporting"
    
    print("--- PostgreSQL Connection Test ---")
    print(f"Host: {pg_host}")
    print(f"Port: {pg_port}")
    print(f"User: {pg_user}")
    print(f"Target DB: {db_name}")
    
    # 1. Connect to default db to create our target database
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if DB exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        if not exists:
            print(f"Database '{db_name}' does not exist. Creating...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"FAILED TO CONNECT OR CREATE DATABASE: {e}")
        sys.exit(1)
        
    # 2. Connect to the target DB and create schemas
    try:
        conn_target = psycopg2.connect(
            dbname=db_name,
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port
        )
        conn_target.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor_target = conn_target.cursor()
        
        schemas = ["staging", "clean", "analytics", "quality"]
        for schema in schemas:
            cursor_target.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            print(f"Schema '{schema}' ensured.")
            
        cursor_target.close()
        conn_target.close()
    except Exception as e:
        print(f"FAILED TO CREATE SCHEMAS: {e}")
        sys.exit(1)

    # 3. Load Data into Staging
    print("\n--- Loading Staging Tables ---")
    
    import urllib.parse
    encoded_password = urllib.parse.quote_plus(pg_password)
    engine = create_engine(f"postgresql+psycopg2://{pg_user}:{encoded_password}@{pg_host}:{pg_port}/{db_name}")
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
    
    # Files to include
    target_files = {
        "customers": "olist_customers_dataset.csv",
        "orders": "olist_orders_dataset.csv",
        "order_items": "olist_order_items_dataset.csv",
        "order_payments": "olist_order_payments_dataset.csv",
        "order_reviews": "olist_order_reviews_dataset.csv",
        "products": "olist_products_dataset.csv",
        "sellers": "olist_sellers_dataset.csv",
        "product_category_name_translation": "product_category_name_translation.csv"
    }
    
    for table_name, filename in target_files.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            print(f"ERROR: File {filename} not found.")
            continue
            
        print(f"Loading {filename} into staging.{table_name}...")
        df = pd.read_csv(filepath)
        source_count = len(df)
        
        # Idempotent load: replace the table
        df.to_sql(table_name, engine, schema="staging", if_exists="replace", index=False)
        
        # Verify row count in DB
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM staging.{table_name}"))
            db_count = result.scalar()
            
        print(f"  Source Rows: {source_count} | Staging Rows: {db_count} -> {'OK' if source_count == db_count else 'MISMATCH'}")
        
    print("\nSUCCESS: Phase 2 Foundation completed.")

if __name__ == "__main__":
    main()
