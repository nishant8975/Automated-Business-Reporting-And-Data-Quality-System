import os
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
    conn.autocommit = True
    cursor = conn.cursor()

    views_sql = [
        """
        CREATE OR REPLACE VIEW analytics.v_order_kpis AS
        WITH items_agg AS (
            SELECT sum(price) as gmv, sum(freight_value) as total_freight, count(*) as total_items
            FROM clean.order_items
        ),
        orders_agg AS (
            SELECT count(DISTINCT order_id) as total_orders
            FROM clean.orders
        ),
        customers_agg AS (
            SELECT count(DISTINCT customer_unique_id) as total_customers,
                   count(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) as repeat_customers
            FROM (
                SELECT c.customer_unique_id, count(DISTINCT o.order_id) as order_count
                FROM clean.customers c
                JOIN clean.orders o ON c.customer_id = o.customer_id
                GROUP BY c.customer_unique_id
            ) c_agg
        ),
        reviews_agg AS (
            SELECT avg(review_score) as average_review_score
            FROM clean.order_reviews
        )
        SELECT 
            o.total_orders,
            c.total_customers,
            i.gmv,
            i.total_freight,
            i.gmv + i.total_freight AS merchandise_plus_freight,
            i.gmv / NULLIF(o.total_orders, 0) AS aov,
            i.total_items,
            c.repeat_customers,
            r.average_review_score
        FROM orders_agg o
        CROSS JOIN customers_agg c
        CROSS JOIN items_agg i
        CROSS JOIN reviews_agg r;
        """,
        """
        CREATE OR REPLACE VIEW analytics.v_monthly_sales AS
        WITH order_base AS (
            SELECT order_id, date_trunc('month', order_purchase_timestamp) as order_month
            FROM clean.orders
        ),
        items_agg AS (
            SELECT order_id, sum(price) as gmv, sum(freight_value) as freight
            FROM clean.order_items
            GROUP BY order_id
        )
        SELECT 
            o.order_month,
            count(DISTINCT o.order_id) as total_orders,
            sum(i.gmv) as gmv,
            sum(i.freight) as total_freight,
            sum(i.gmv + i.freight) as merchandise_plus_freight,
            sum(i.gmv) / NULLIF(count(DISTINCT o.order_id), 0) as aov
        FROM order_base o
        LEFT JOIN items_agg i ON o.order_id = i.order_id
        GROUP BY o.order_month
        ORDER BY o.order_month;
        """,
        """
        CREATE OR REPLACE VIEW analytics.v_category_sales AS
        WITH items_with_cat AS (
            SELECT 
                i.order_id,
                COALESCE(p.product_category_name, 'Unknown') as product_category,
                i.price,
                i.freight_value
            FROM clean.order_items i
            LEFT JOIN clean.products p ON i.product_id = p.product_id
        )
        SELECT 
            product_category,
            count(*) as total_items,
            sum(price) as gmv,
            sum(freight_value) as total_freight,
            sum(price + freight_value) as merchandise_plus_freight,
            count(DISTINCT order_id) as order_count
        FROM items_with_cat
        GROUP BY product_category
        ORDER BY gmv DESC;
        """,
        """
        CREATE OR REPLACE VIEW analytics.v_payment_analysis AS
        SELECT 
            payment_type,
            count(DISTINCT order_id) as total_orders,
            count(*) as payment_transaction_count,
            sum(payment_value) as total_payment_value,
            avg(payment_value) as average_payment_value
        FROM clean.order_payments
        GROUP BY payment_type
        ORDER BY total_payment_value DESC;
        """,
        """
        CREATE OR REPLACE VIEW analytics.v_review_analysis AS
        SELECT 
            review_score,
            count(*) as review_count
        FROM clean.order_reviews
        GROUP BY review_score
        ORDER BY review_score DESC;
        """,
        """
        CREATE OR REPLACE VIEW analytics.v_order_status AS
        WITH total_o AS (SELECT count(*) as t FROM clean.orders)
        SELECT 
            o.order_status,
            count(*) as total_orders,
            (count(*) * 100.0 / NULLIF(t.t, 0)) as percentage_of_orders
        FROM clean.orders o
        CROSS JOIN total_o t
        GROUP BY o.order_status, t.t
        ORDER BY total_orders DESC;
        """,
        """
        CREATE OR REPLACE VIEW analytics.v_customer_analysis AS
        WITH cust_orders AS (
            SELECT 
                c.customer_unique_id,
                o.order_id,
                o.order_purchase_timestamp
            FROM clean.customers c
            JOIN clean.orders o ON c.customer_id = o.customer_id
        ),
        items_agg AS (
            SELECT order_id, sum(price) as gmv
            FROM clean.order_items
            GROUP BY order_id
        )
        SELECT 
            co.customer_unique_id,
            count(DISTINCT co.order_id) as total_orders,
            sum(i.gmv) as total_gmv,
            min(co.order_purchase_timestamp) as first_order_date,
            max(co.order_purchase_timestamp) as last_order_date,
            CASE WHEN count(DISTINCT co.order_id) > 1 THEN 'Repeat' ELSE 'One-Time' END as customer_type
        FROM cust_orders co
        LEFT JOIN items_agg i ON co.order_id = i.order_id
        GROUP BY co.customer_unique_id
        ORDER BY total_gmv DESC;
        """,
        """
        CREATE OR REPLACE VIEW analytics.v_data_quality_summary AS
        SELECT
            (SELECT COUNT(*) FROM quality.invalid_records) as total_invalid_records,
            (SELECT COUNT(*) FROM quality.invalid_records WHERE source_table = 'products') as invalid_product_records,
            (SELECT COUNT(*) FROM quality.invalid_records WHERE source_table = 'order_payments') as invalid_payment_records,
            (SELECT COUNT(*) FROM clean.orders WHERE is_order_approved_at_valid = FALSE OR is_order_delivered_carrier_date_valid = FALSE OR is_order_delivered_customer_date_valid = FALSE) as orders_with_timestamp_anomalies,
            (SELECT COUNT(*) FROM clean.products WHERE product_category_name IS NULL) as products_with_missing_category,
            (SELECT COUNT(*) FROM clean.orders WHERE is_order_approved_at_valid = TRUE) * 100.0 / NULLIF((SELECT COUNT(*) FROM clean.orders WHERE is_order_approved_at_valid IS NOT NULL), 0) as valid_order_timestamp_percentage
        """
    ]

    for sql in views_sql:
        cursor.execute(sql)

    print("ALL VIEWS CREATED SUCCESSFULLY.")
    
    # RECONCILIATION
    def exec_val(q):
        cursor.execute(q)
        return cursor.fetchone()[0]

    print("\n--- KPI RECONCILIATION ---")
    
    # 1. GMV
    gmv_base = exec_val("SELECT SUM(price) FROM clean.order_items;")
    gmv_kpi = exec_val("SELECT gmv FROM analytics.v_order_kpis;")
    print(f"GMV        - Base: {gmv_base}, KPI: {gmv_kpi} -> Match: {gmv_base == gmv_kpi}")
    
    # 2. Freight
    freight_base = exec_val("SELECT SUM(freight_value) FROM clean.order_items;")
    freight_kpi = exec_val("SELECT total_freight FROM analytics.v_order_kpis;")
    print(f"Freight    - Base: {freight_base}, KPI: {freight_kpi} -> Match: {freight_base == freight_kpi}")
    
    # 3. Orders
    orders_base = exec_val("SELECT COUNT(DISTINCT order_id) FROM clean.orders;")
    orders_kpi = exec_val("SELECT total_orders FROM analytics.v_order_kpis;")
    print(f"Orders     - Base: {orders_base}, KPI: {orders_kpi} -> Match: {orders_base == orders_kpi}")
    
    # 4. Customers
    cust_base = exec_val("SELECT COUNT(DISTINCT customer_unique_id) FROM clean.customers;")
    cust_kpi = exec_val("SELECT total_customers FROM analytics.v_order_kpis;")
    print(f"Customers  - Base: {cust_base}, KPI: {cust_kpi} -> Match: {cust_base == cust_kpi}")
    
    # 5. Payments
    pay_base = exec_val("SELECT SUM(payment_value) FROM clean.order_payments;")
    pay_kpi = exec_val("SELECT SUM(total_payment_value) FROM analytics.v_payment_analysis;")
    print(f"Payments   - Base: {pay_base}, KPI: {pay_kpi} -> Match: {pay_base == pay_kpi}")
    
    # 6. Category GMV
    cat_gmv = exec_val("SELECT SUM(gmv) FROM analytics.v_category_sales;")
    print(f"Cat GMV    - Match with Base: {cat_gmv == gmv_base}")
    
    # 7. Monthly GMV
    month_gmv = exec_val("SELECT SUM(gmv) FROM analytics.v_monthly_sales;")
    print(f"Month GMV  - Match with Base: {month_gmv == gmv_base}")
    
    # 8. Monthly Orders
    # Not a straight sum since an order might not have a month if it is NULL, but let's check
    month_orders = exec_val("SELECT SUM(total_orders) FROM analytics.v_monthly_sales;")
    print(f"Mth Orders - Match with Base: {month_orders == orders_base}")

    cursor.execute("SELECT * FROM analytics.v_order_kpis")
    kpis = cursor.fetchone()
    cols = [desc[0] for desc in cursor.description]
    print("\n--- KPI RESULTS ---")
    for col, val in zip(cols, kpis):
        print(f"{col}: {val}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
