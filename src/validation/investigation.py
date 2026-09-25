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

def main():
    conn = get_conn()
    
    # -----------------------------------------------------
    # INVESTIGATION 1 & 3: Order Timestamp Anomalies
    # -----------------------------------------------------
    print("=== INVESTIGATION 1: ORDER TIMESTAMP ANOMALIES ===")
    
    query_a = """
        SELECT *
        FROM staging.orders
        WHERE order_purchase_timestamp IS NOT NULL
          AND order_approved_at IS NOT NULL
          AND order_delivered_carrier_date IS NOT NULL
          AND CAST(order_approved_at AS TIMESTAMP) > CAST(order_delivered_carrier_date AS TIMESTAMP)
    """
    
    query_b = """
        SELECT *
        FROM staging.orders
        WHERE order_purchase_timestamp IS NOT NULL
          AND order_delivered_carrier_date IS NOT NULL
          AND order_delivered_customer_date IS NOT NULL
          AND CAST(order_delivered_carrier_date AS TIMESTAMP) > CAST(order_delivered_customer_date AS TIMESTAMP)
    """
    
    df_a = pd.read_sql(query_a, conn)
    df_b = pd.read_sql(query_b, conn)
    
    # Distinct counts
    a_orders = set(df_a['order_id'])
    b_orders = set(df_b['order_id'])
    
    print(f"Violation A (approved > carrier): {len(a_orders)} distinct orders")
    print(f"Violation B (carrier > customer): {len(b_orders)} distinct orders")
    
    overlap = a_orders.intersection(b_orders)
    print(f"Overlap between A and B: {len(overlap)} distinct orders")
    
    total_affected = len(a_orders.union(b_orders))
    print(f"Total distinct orders affected: {total_affected}")
    
    total_query = "SELECT COUNT(DISTINCT order_id) FROM staging.orders"
    df_total = pd.read_sql(total_query, conn)
    total_orders = df_total.iloc[0, 0]
    print(f"Total distinct orders NOT affected: {total_orders - total_affected}\n")
    
    df_combined = pd.concat([df_a, df_b]).drop_duplicates(subset=['order_id'])
    
    status_counts = df_combined['order_status'].value_counts(normalize=False)
    status_pct = df_combined['order_status'].value_counts(normalize=True) * 100
    print("Status distribution of affected orders:")
    for status, count in status_counts.items():
        print(f" - {status}: {count} ({status_pct[status]:.2f}%)")
    
    print("\nExamples of affected orders (Violation A):")
    cols_to_show = ['order_id', 'order_status', 'order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date']
    if not df_a.empty:
        print(df_a.head(3)[cols_to_show].to_string())
        
    print("\nExamples of affected orders (Violation B):")
    if not df_b.empty:
        print(df_b.head(3)[cols_to_show].to_string())
        
    print("\n=== INVESTIGATION 3: IMPACT ON ANALYTICS ===")
    
    affected_tuple = tuple(a_orders.union(b_orders))
    if affected_tuple:
        # Check items
        q_items = f"""
            SELECT COUNT(DISTINCT order_id) FROM staging.order_items 
            WHERE order_id IN %s
        """
        items_cursor = conn.cursor()
        items_cursor.execute(q_items, (affected_tuple,))
        orders_with_items = items_cursor.fetchone()[0]
        
        q_pos_price = f"""
            SELECT COUNT(DISTINCT order_id) FROM staging.order_items 
            WHERE order_id IN %s AND CAST(price AS NUMERIC) > 0
        """
        items_cursor.execute(q_pos_price, (affected_tuple,))
        orders_with_pos_price = items_cursor.fetchone()[0]
        
        q_payments = f"""
            SELECT COUNT(DISTINCT order_id) FROM staging.order_payments 
            WHERE order_id IN %s
        """
        items_cursor.execute(q_payments, (affected_tuple,))
        orders_with_payments = items_cursor.fetchone()[0]
        
        q_customers = f"""
            SELECT COUNT(DISTINCT o.order_id)
            FROM staging.orders o
            JOIN staging.customers c ON o.customer_id = c.customer_id
            WHERE o.order_id IN %s
        """
        items_cursor.execute(q_customers, (affected_tuple,))
        orders_with_valid_customers = items_cursor.fetchone()[0]
        
        print(f"Affected orders with items: {orders_with_items}")
        print(f"Affected orders with positive item price: {orders_with_pos_price}")
        print(f"Affected orders with payments: {orders_with_payments}")
        print(f"Affected orders with valid customer relationship: {orders_with_valid_customers}")

    # -----------------------------------------------------
    # INVESTIGATION 2: Product Validation Overlap
    # -----------------------------------------------------
    print("\n=== INVESTIGATION 2: PRODUCT VALIDATION OVERLAP ===")
    
    q_prod_dim = """
        SELECT product_id, product_weight_g, product_length_cm, product_height_cm, product_width_cm
        FROM staging.products
        WHERE product_weight_g IS NULL
           OR product_length_cm IS NULL
           OR product_height_cm IS NULL
           OR product_width_cm IS NULL
    """
    df_prod_dim = pd.read_sql(q_prod_dim, conn)
    
    q_prod_w = """
        SELECT product_id, product_weight_g, product_length_cm, product_height_cm, product_width_cm
        FROM staging.products
        WHERE product_weight_g IS NOT NULL AND CAST(product_weight_g AS NUMERIC) <= 0
    """
    df_prod_w = pd.read_sql(q_prod_w, conn)
    
    set_dim = set(df_prod_dim['product_id'])
    set_w = set(df_prod_w['product_id'])
    
    print(f"Products with missing dims: {len(set_dim)}")
    print(f"Products with non-positive weight: {len(set_w)}")
    print(f"Intersection: {len(set_dim.intersection(set_w))}")
    print(f"Total distinct products requiring action: {len(set_dim.union(set_w))}")
    
    df_prod_combined = pd.concat([df_prod_dim, df_prod_w]).drop_duplicates(subset=['product_id'])
    print("\nAffected Products:")
    print(df_prod_combined.to_string())

    conn.close()

if __name__ == "__main__":
    main()
