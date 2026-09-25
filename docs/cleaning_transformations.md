# Cleaning and Transformations

This document records the exact transformations applied to move data from the `staging` schema to the `clean` schema.

## 1. Type Casting
- **Rule:** Convert text-based fields from staging to their proper analytical data types.
- **Transformations:**
  - `price`, `freight_value`, `payment_value` cast to `NUMERIC`.
  - All date/time fields (`order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`, `shipping_limit_date`, `review_creation_date`, `review_answer_timestamp`) cast to `TIMESTAMP`.
  - ID fields and categorical fields kept as `TEXT`.
  - Sequence/numeric counts (like `payment_installments`, `payment_sequential`, `product_weight_g`, etc.) cast to integer or numeric types appropriately.
- **Reason:** To enable mathematical aggregations and chronological date filtering.

## 2. Order Timestamps Anomaly Resolution
- **Source:** `staging.orders`
- **Target:** `clean.orders`
- **Original Condition:** 1,359 orders where `approved_at > carrier_date` and 23 orders where `carrier_date > customer_date`.
- **Transformation:** 
  - Added boolean validity flags: `is_order_approved_at_valid`, `is_order_delivered_carrier_date_valid`, `is_order_delivered_customer_date_valid`.
  - Flags are set to `FALSE` when a timestamp violates the chronological rule (e.g. `order_delivered_carrier_date < order_approved_at` sets `is_order_delivered_carrier_date_valid = FALSE`).
  - When a flag is `FALSE`, the corresponding timestamp is set to `NULL` in the clean layer, otherwise it retains the staging value.
  - The parent order is kept intact to prevent losing valid sales and items.
- **Affected Row Count:** 1,382 total orders have at least one timestamp nullified and flagged.
- **Preservation:** The raw incorrect timestamps are preserved in `staging.orders`.
- **KPI Impact:** Does not affect revenue or volume KPIs. Ensures delivery-time metrics are not corrupted by negative durations.

## 3. Product Dimension/Weight Quarantine
- **Source:** `staging.products`
- **Target:** `quality.invalid_records`, `clean.products`
- **Original Condition:** 2 products with missing dimensions, 4 products with `weight <= 0`.
- **Transformation:**
  - The 6 raw records are inserted into `quality.invalid_records`.
  - In `clean.products`, these 6 products are still inserted (to prevent breaking referential integrity for `order_items`), but their invalid attributes (weight, length, height, width) are set to `NULL` to prevent analytics corruption.
- **Reason:** Products must be quarantined for physical analysis, but their IDs must exist in the clean layer so sales (GMV) tied to these products are not lost.
- **Affected Row Count:** 6 products.
- **KPI Impact:** Preserves revenue GMV while preventing averages of invalid physical dimensions.

## 4. Payment Installment Quarantine
- **Source:** `staging.order_payments`
- **Target:** `quality.invalid_records`, excluded from `clean.order_payments`
- **Original Condition:** 2 records with `payment_installments < 1`.
- **Transformation:** 
  - Exclude the 2 invalid payment rows from `clean.order_payments`.
  - Insert the 2 raw records into `quality.invalid_records`.
- **Reason:** Installments must be >= 1. The parent order is not deleted.
- **Affected Row Count:** 2 payments excluded.
- **KPI Impact:** Reduces total payment value slightly (by removing 2 rows), but does not affect GMV (which is calculated from `order_items`).

## 5. Missing Product Categories
- **Source:** `staging.products`
- **Target:** `clean.products`
- **Original Condition:** 610 products have a `NULL` category.
- **Transformation:** Left as `NULL` in the clean table.
- **Reason:** Legitimate missing data. Will be handled via `COALESCE` in analytical views.
- **Affected Row Count:** 610 products.
- **KPI Impact:** None on GMV, allows dynamic fallback logic in reporting.
