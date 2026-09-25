# Data Quality Report

## 1. Executive Summary
- Total Validation Rules: 69
- PASS: 55
- WARN: 6
- FAIL: 8

## 2. Validation Results

| Rule ID | Table | Column/Check | Dimension | Total | Failed | % | Status |
|---|---|---|---|---|---|---|---|
| COMP-customers-customer_id | customers | customer_id | COMPLETENESS | 99441 | 0 | 0.00% | PASS |
| COMP-customers-customer_unique_id | customers | customer_unique_id | COMPLETENESS | 99441 | 0 | 0.00% | PASS |
| COMP-customers-customer_zip_code_prefix | customers | customer_zip_code_prefix | COMPLETENESS | 99441 | 0 | 0.00% | PASS |
| COMP-customers-customer_city | customers | customer_city | COMPLETENESS | 99441 | 0 | 0.00% | PASS |
| COMP-customers-customer_state | customers | customer_state | COMPLETENESS | 99441 | 0 | 0.00% | PASS |
| COMP-orders-order_id | orders | order_id | COMPLETENESS | 99441 | 0 | 0.00% | PASS |
| COMP-orders-customer_id | orders | customer_id | COMPLETENESS | 99441 | 0 | 0.00% | PASS |
| COMP-orders-order_status | orders | order_status | COMPLETENESS | 99441 | 0 | 0.00% | PASS |
| COMP-orders-order_purchase_timestamp | orders | order_purchase_timestamp | COMPLETENESS | 99441 | 0 | 0.00% | PASS |
| COMP-orders-order_approved_at | orders | order_approved_at | COMPLETENESS | 99441 | 160 | 0.16% | WARN |
| COMP-orders-order_delivered_carrier_date | orders | order_delivered_carrier_date | COMPLETENESS | 99441 | 1783 | 1.79% | WARN |
| COMP-orders-order_delivered_customer_date | orders | order_delivered_customer_date | COMPLETENESS | 99441 | 2965 | 2.98% | WARN |
| COMP-orders-order_estimated_delivery_date | orders | order_estimated_delivery_date | COMPLETENESS | 99441 | 0 | 0.00% | PASS |
| COMP-order_items-order_id | order_items | order_id | COMPLETENESS | 112650 | 0 | 0.00% | PASS |
| COMP-order_items-order_item_id | order_items | order_item_id | COMPLETENESS | 112650 | 0 | 0.00% | PASS |
| COMP-order_items-product_id | order_items | product_id | COMPLETENESS | 112650 | 0 | 0.00% | PASS |
| COMP-order_items-seller_id | order_items | seller_id | COMPLETENESS | 112650 | 0 | 0.00% | PASS |
| COMP-order_items-shipping_limit_date | order_items | shipping_limit_date | COMPLETENESS | 112650 | 0 | 0.00% | PASS |
| COMP-order_items-price | order_items | price | COMPLETENESS | 112650 | 0 | 0.00% | PASS |
| COMP-order_items-freight_value | order_items | freight_value | COMPLETENESS | 112650 | 0 | 0.00% | PASS |
| COMP-order_payments-order_id | order_payments | order_id | COMPLETENESS | 103886 | 0 | 0.00% | PASS |
| COMP-order_payments-payment_sequential | order_payments | payment_sequential | COMPLETENESS | 103886 | 0 | 0.00% | PASS |
| COMP-order_payments-payment_type | order_payments | payment_type | COMPLETENESS | 103886 | 0 | 0.00% | PASS |
| COMP-order_payments-payment_installments | order_payments | payment_installments | COMPLETENESS | 103886 | 0 | 0.00% | PASS |
| COMP-order_payments-payment_value | order_payments | payment_value | COMPLETENESS | 103886 | 0 | 0.00% | PASS |
| COMP-order_reviews-review_id | order_reviews | review_id | COMPLETENESS | 99224 | 0 | 0.00% | PASS |
| COMP-order_reviews-order_id | order_reviews | order_id | COMPLETENESS | 99224 | 0 | 0.00% | PASS |
| COMP-order_reviews-review_score | order_reviews | review_score | COMPLETENESS | 99224 | 0 | 0.00% | PASS |
| COMP-order_reviews-review_creation_date | order_reviews | review_creation_date | COMPLETENESS | 99224 | 0 | 0.00% | PASS |
| COMP-order_reviews-review_answer_timestamp | order_reviews | review_answer_timestamp | COMPLETENESS | 99224 | 0 | 0.00% | PASS |
| COMP-order_reviews-review_comment_title | order_reviews | review_comment_title | COMPLETENESS | 99224 | 87656 | 88.34% | WARN |
| COMP-order_reviews-review_comment_message | order_reviews | review_comment_message | COMPLETENESS | 99224 | 58247 | 58.70% | WARN |
| COMP-products-product_id | products | product_id | COMPLETENESS | 32951 | 0 | 0.00% | PASS |
| COMP-products-product_category_name | products | product_category_name | COMPLETENESS | 32951 | 610 | 1.85% | WARN |
| COMP-products-product_weight_g | products | product_weight_g | COMPLETENESS | 32951 | 2 | 0.01% | FAIL |
| COMP-products-product_length_cm | products | product_length_cm | COMPLETENESS | 32951 | 2 | 0.01% | FAIL |
| COMP-products-product_height_cm | products | product_height_cm | COMPLETENESS | 32951 | 2 | 0.01% | FAIL |
| COMP-products-product_width_cm | products | product_width_cm | COMPLETENESS | 32951 | 2 | 0.01% | FAIL |
| COMP-sellers-seller_id | sellers | seller_id | COMPLETENESS | 3095 | 0 | 0.00% | PASS |
| COMP-sellers-seller_zip_code_prefix | sellers | seller_zip_code_prefix | COMPLETENESS | 3095 | 0 | 0.00% | PASS |
| COMP-sellers-seller_city | sellers | seller_city | COMPLETENESS | 3095 | 0 | 0.00% | PASS |
| COMP-sellers-seller_state | sellers | seller_state | COMPLETENESS | 3095 | 0 | 0.00% | PASS |
| UNIQ-customers | customers | customer_id | UNIQUENESS | 99441 | 0 | 0.00% | PASS |
| UNIQ-orders | orders | order_id | UNIQUENESS | 99441 | 0 | 0.00% | PASS |
| UNIQ-order_items | order_items | order_id, order_item_id | UNIQUENESS | 112650 | 0 | 0.00% | PASS |
| UNIQ-order_payments | order_payments | order_id, payment_sequential | UNIQUENESS | 103886 | 0 | 0.00% | PASS |
| UNIQ-order_reviews | order_reviews | review_id, order_id | UNIQUENESS | 99224 | 0 | 0.00% | PASS |
| UNIQ-products | products | product_id | UNIQUENESS | 32951 | 0 | 0.00% | PASS |
| UNIQ-sellers | sellers | seller_id | UNIQUENESS | 3095 | 0 | 0.00% | PASS |
| UNIQ-product_category_name_translation | product_category_name_translation | product_category_name | UNIQUENESS | 71 | 0 | 0.00% | PASS |
| REF-orders-customers | orders | customer_id | REFERENTIAL | 99441 | 0 | 0.00% | PASS |
| REF-order_items-orders | order_items | order_id | REFERENTIAL | 112650 | 0 | 0.00% | PASS |
| REF-order_items-products | order_items | product_id | REFERENTIAL | 112650 | 0 | 0.00% | PASS |
| REF-order_items-sellers | order_items | seller_id | REFERENTIAL | 112650 | 0 | 0.00% | PASS |
| REF-order_payments-orders | order_payments | order_id | REFERENTIAL | 103886 | 0 | 0.00% | PASS |
| REF-order_reviews-orders | order_reviews | order_id | REFERENTIAL | 99224 | 0 | 0.00% | PASS |
| DOM-order_items-price | order_items | price | VALIDITY | 112650 | 0 | 0.00% | PASS |
| DOM-order_items-freight_value | order_items | freight_value | VALIDITY | 112650 | 0 | 0.00% | PASS |
| DOM-order_payments-payment_value | order_payments | payment_value | VALIDITY | 103886 | 0 | 0.00% | PASS |
| DOM-order_payments-payment_installments | order_payments | payment_installments | VALIDITY | 103886 | 2 | 0.00% | FAIL |
| DOM-order_payments-payment_sequential | order_payments | payment_sequential | VALIDITY | 103886 | 0 | 0.00% | PASS |
| DOM-order_reviews-review_score | order_reviews | review_score | VALIDITY | 99224 | 0 | 0.00% | PASS |
| DOM-products-product_weight_g | products | product_weight_g | VALIDITY | 32949 | 4 | 0.01% | FAIL |
| DOM-products-product_length_cm | products | product_length_cm | VALIDITY | 32949 | 0 | 0.00% | PASS |
| DOM-products-product_height_cm | products | product_height_cm | VALIDITY | 32949 | 0 | 0.00% | PASS |
| DOM-products-product_width_cm | products | product_width_cm | VALIDITY | 32949 | 0 | 0.00% | PASS |
| DATE-order_purchase_timestamp <= order_approved_at | orders | order_purchase_timestamp <= order_approved_at | CONSISTENCY | 99441 | 0 | 0.00% | PASS |
| DATE-order_approved_at <= order_delivered_carrier_date | orders | order_approved_at <= order_delivered_carrier_date | CONSISTENCY | 99441 | 1350 | 1.36% | FAIL |
| DATE-order_delivered_carrier_date <= order_delivered_customer_date | orders | order_delivered_carrier_date <= order_delivered_customer_date | CONSISTENCY | 99441 | 23 | 0.02% | FAIL |
