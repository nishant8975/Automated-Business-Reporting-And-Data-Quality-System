# Analytics Layer

This document details the PostgreSQL analytics layer, which provides the final business KPIs for reporting (Excel, Power BI, Python).

## 1. Purpose
The analytics layer transforms the normalized `clean` schema into aggregated, business-ready views. It is specifically designed to prevent data fan-out by strictly controlling the granularity of each view.

## 2. Views and Grain

| View Name | Grain | Description |
| :--- | :--- | :--- |
| `v_order_kpis` | 1 Row Total | The master KPI summary (GMV, AOV, Total Orders, etc). |
| `v_monthly_sales` | `order_month` | Time-series aggregation for monthly trends. |
| `v_category_sales` | `product_category` | Sales sliced by product category. |
| `v_payment_analysis` | `payment_type` | Orders and payment totals sliced by payment method. |
| `v_review_analysis` | `review_score` | Distribution of customer review scores (1-5). |
| `v_order_status` | `order_status` | Breakdown of orders by fulfillment status. |
| `v_customer_analysis` | `customer_unique_id` | Customer lifetime value and repeat purchase behavior. |
| `v_data_quality_summary` | 1 Row Total | Exposure of data quality findings and quarantine volumes. |

## 3. KPI Definitions & Treatments

- **Total Orders:** `COUNT(DISTINCT order_id)` from `clean.orders`.
- **Total Customers:** `COUNT(DISTINCT customer_unique_id)` from `clean.customers`.
- **GMV (Gross Merchandise Value):** `SUM(price)` from `clean.order_items`. It strictly excludes freight and payment variations.
- **Payment Totals:** `SUM(payment_value)` from `clean.order_payments`.
- **Customer Unique ID Treatment:** Lifetime value is calculated by joining `orders` to `customers` and grouping by `customer_unique_id`, which correctly clusters repeat purchases by the same individual.
- **Unknown Category Treatment:** Products missing a category use `COALESCE(product_category_name, 'Unknown')` in `v_category_sales`.

## 4. Fan-Out Prevention Strategy
We strictly avoid doing large flat joins (e.g., `orders` JOIN `order_items` JOIN `order_payments`). Since an order can have multiple items and multiple payments, a flat join creates cartesian explosion (fan-out).

Instead, views pre-aggregate child tables (like `order_items` or `order_payments`) to the `order_id` level inside CTEs *before* joining them to the parent `orders` table.

## 5. Reconciliation Checks
To guarantee safety, we executed independent scalar checks comparing the base clean tables against the final analytics views:
1. `analytics.v_order_kpis.gmv` == `SUM(price) FROM clean.order_items`
2. `analytics.v_order_kpis.total_freight` == `SUM(freight_value) FROM clean.order_items`
3. `analytics.v_order_kpis.total_orders` == `COUNT(DISTINCT order_id) FROM clean.orders`
4. `analytics.v_category_sales.gmv` == `SUM(price) FROM clean.order_items`
5. `analytics.v_payment_analysis.total_payment_value` == `SUM(payment_value) FROM clean.order_payments`

All reconciliation checks perfectly matched.

## 6. Known Limitations
- The monthly sales view truncates to the `order_purchase_timestamp`. Any orders missing a purchase timestamp will fall into a `NULL` month bucket.
- Payment totals (`v_payment_analysis`) will naturally differ from GMV. Payment value exceeds merchandise + freight by $165,130.25. The current dataset does not provide sufficient evidence to attribute this difference to specific factors, so payment value is retained as a separate payment/reconciliation metric rather than being used as the primary GMV measure.
