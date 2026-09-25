# Data Quality Rule Catalog

This document defines the rules applied to validate the raw staging data. These rules dictate which records are deemed valid for the `clean` layer, and which should be quarantined into `quality.invalid_records`.

---

## 1. DQ-COMPLETENESS (Completeness Checks)

| Rule ID | Table | Column | Expected Condition | Severity | Action if Failed | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| COMP-customers-id | `customers` | `customer_id` | Not NULL | HIGH | Quarantine Row | PK required for order relationship. |
| COMP-customers-uniq | `customers` | `customer_unique_id` | Not NULL | HIGH | Quarantine Row | Required for repeat customer metrics. |
| COMP-orders-id | `orders` | `order_id` | Not NULL | HIGH | Quarantine Row | PK required to identify order. |
| COMP-orders-customer | `orders` | `customer_id` | Not NULL | HIGH | Quarantine Row | FK required for customer relationship. |
| COMP-orders-status | `orders` | `order_status` | Not NULL | HIGH | Quarantine Row | Required to filter analytical population. |
| COMP-orders-purch | `orders` | `order_purchase_timestamp` | Not NULL | HIGH | Quarantine Row | Required for timeline / revenue cohorting. |
| COMP-orders-deliv | `orders` | `order_delivered_customer_date`| Not NULL | LOW | Keep | Valid status for processing/cancelled orders. |
| COMP-items-id | `order_items` | `order_item_id` | Not NULL | HIGH | Quarantine Row | PK required. |
| COMP-items-prod | `order_items` | `product_id` | Not NULL | HIGH | Quarantine Row | FK required for product metrics. |
| COMP-items-price | `order_items` | `price` | Not NULL | HIGH | Quarantine Row | Required for GMV calculations. |
| COMP-items-freight| `order_items` | `freight_value` | Not NULL | HIGH | Quarantine Row | Required for total value calculations. |
| COMP-pay-seq | `order_payments` | `payment_sequential` | Not NULL | HIGH | Quarantine Row | PK required. |
| COMP-pay-val | `order_payments` | `payment_value` | Not NULL | HIGH | Quarantine Row | Required for payment reconciliation. |
| COMP-rev-score | `order_reviews` | `review_score` | Not NULL | HIGH | Quarantine Row | Required for review analysis. |
| COMP-rev-title | `order_reviews` | `review_comment_title` | Not NULL | LOW | Keep | Optional field, sparsity expected. |
| COMP-rev-msg | `order_reviews` | `review_comment_message` | Not NULL | LOW | Keep | Optional field, sparsity expected. |
| COMP-prod-cat | `products` | `product_category_name` | Not NULL | LOW | Map to 'Unknown' | Products can legitimately lack category. |

## 2. DQ-UNIQUENESS (Uniqueness Checks)

| Rule ID | Table | Column(s) | Expected Condition | Severity | Action if Failed | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| UNIQ-customers | `customers` | `customer_id` | Unique | HIGH | Quarantine Duplicate | Enforce 1:1 with orders. |
| UNIQ-orders | `orders` | `order_id` | Unique | HIGH | Quarantine Duplicate | Enforce PK. |
| UNIQ-order_items | `order_items` | `order_id`, `order_item_id` | Unique | HIGH | Quarantine Duplicate | Enforce PK. |
| UNIQ-order_payments | `order_payments`| `order_id`, `payment_sequential`| Unique | HIGH | Quarantine Duplicate | Enforce PK. |
| UNIQ-order_reviews | `order_reviews` | `review_id`, `order_id` | Unique | HIGH | Quarantine Duplicate | Enforce PK. |
| UNIQ-products | `products` | `product_id` | Unique | HIGH | Quarantine Duplicate | Enforce PK. |
| UNIQ-sellers | `sellers` | `seller_id` | Unique | HIGH | Quarantine Duplicate | Enforce PK. |

## 3. DQ-REFERENTIAL (Referential Integrity Checks)

| Rule ID | Table | FK Column | Expected Condition | Severity | Action if Failed | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| REF-orders-customers| `orders` | `customer_id` | Exists in `customers` | HIGH | Quarantine Row | Orders must map to valid customer record. |
| REF-order_items-orders | `order_items` | `order_id` | Exists in `orders` | HIGH | Quarantine Row | Items must belong to a valid order. |
| REF-order_items-products| `order_items`| `product_id` | Exists in `products` | HIGH | Quarantine Row | Items must map to valid product. |
| REF-order_items-sellers| `order_items` | `seller_id` | Exists in `sellers` | HIGH | Quarantine Row | Items must map to valid seller. |
| REF-order_payments-orders| `order_payments`| `order_id` | Exists in `orders` | HIGH | Quarantine Row | Payments must belong to a valid order. |
| REF-order_reviews-orders| `order_reviews`| `order_id` | Exists in `orders` | HIGH | Quarantine Row | Reviews must belong to a valid order. |

## 4. DQ-VALIDITY (Domain/Numeric Validity Checks)

| Rule ID | Table | Column | Expected Condition | Severity | Action if Failed | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DOM-order_items-price | `order_items` | `price` | `>= 0` | HIGH | Quarantine Row | Price cannot be negative. |
| DOM-order_items-freight | `order_items` | `freight_value` | `>= 0` | HIGH | Quarantine Row | Freight cannot be negative. |
| DOM-order_payments-value | `order_payments` | `payment_value` | `>= 0` | HIGH | Quarantine Row | Payments cannot be negative. |
| DOM-order_payments-install | `order_payments` | `payment_installments` | `>= 1` | HIGH | Quarantine Row | Installments must be at least 1. |
| DOM-order_reviews-score | `order_reviews` | `review_score` | `BETWEEN 1 AND 5` | HIGH | Quarantine Row | Review scores use 5-point scale. |
| DOM-products-weight | `products` | `product_weight_g` | `> 0` | HIGH | Quarantine Row | Physical products must have mass. |

## 5. DQ-CONSISTENCY (Date/Timestamp Checks)

| Rule ID | Table | Columns | Expected Condition | Severity | Action if Failed | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DATE-purchase-approved | `orders` | `order_purchase_timestamp`, `order_approved_at` | Purchase <= Approved | HIGH | Quarantine Row | Order must be placed before approval. |
| DATE-approved-carrier | `orders` | `order_approved_at`, `order_delivered_carrier_date`| Approved <= Carrier | HIGH | Quarantine Row | Must be approved before carrier pickup. |
| DATE-carrier-customer | `orders` | `order_delivered_carrier_date`, `order_delivered_customer_date`| Carrier <= Customer | HIGH | Quarantine Row | Carrier must pick up before customer receives. |
