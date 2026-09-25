# Data Dictionary

This document details the major fields from the core dataset utilized in the analytical modeling layer.

## `clean.customers`
- `customer_id`: A unique token generated per order. Used to link a specific order to a customer record.
- `customer_unique_id`: The actual, unique identifier of the human being. Used to calculate true customer counts and repeat purchasing behavior.
- `customer_city`: City of the customer.
- `customer_state`: State of the customer.

## `clean.orders`
- `order_id`: Primary key for the transaction.
- `customer_id`: Foreign key to the customer table.
- `order_status`: Status of the order (e.g., delivered, shipped, canceled).
- `order_purchase_timestamp`: The exact date and time the order was placed. Used for all primary time-series and monthly sales analytics.
- `order_approved_at`: Payment approval timestamp. Nullified if illogical (e.g., occurs logically before purchase).
- `order_delivered_carrier_date`: Logistics handoff timestamp. Nullified if illogical.
- `order_delivered_customer_date`: Final delivery timestamp. Nullified if illogical.

## `clean.order_items`
- `order_id`: Foreign key to the order.
- `order_item_id`: Sequential number identifying the number of items within the same order.
- `product_id`: Foreign key to the product.
- `seller_id`: Foreign key to the seller.
- `price`: The merchandise cost of the item. Summed to calculate primary GMV.
- `freight_value`: The shipping cost for this specific item.

## `clean.order_payments`
- `order_id`: Foreign key to the order.
- `payment_sequential`: Sequential number identifying if an order was paid for with multiple methods.
- `payment_type`: Method of payment (e.g., credit card, boleto).
- `payment_installments`: Number of installments chosen by the customer. Validated to be >= 1.
- `payment_value`: Total transaction value processed. Tracked separately from GMV for reconciliation purposes.

## `clean.order_reviews`
- `review_id`: Unique identifier for the review.
- `order_id`: Foreign key to the order being reviewed.
- `review_score`: Customer satisfaction score, ranging from 1 to 5. Used to calculate average satisfaction.

## `clean.products`
- `product_id`: Primary key for the product catalog.
- `product_category_name`: Native Portuguese category name. Missing values are preserved.
- `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`: Physical dimensions. Nullified if invalid or negative, though the product ID remains for order integrity.

## `clean.product_category_name_translation`
- `product_category_name`: Native Portuguese category name.
- `product_category_name_english`: English translation. Used when joining for dashboard localization.
