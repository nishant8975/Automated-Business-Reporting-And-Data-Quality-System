# Data Model Definition

This document outlines the relational data model for the Automated Business Reporting & Data Quality System. It defines the tables, their grain, relationships, and identifies potential double-counting risks when performing analytics.

## 1. Final Table List

| Table Name | Included in MVP | Reason for Inclusion / Exclusion |
| :--- | :---: | :--- |
| `customers` | Yes | Required to analyze customer distribution, repeat customers, and demographics. |
| `orders` | Yes | Core fact table representing order events and fulfillment timelines. |
| `order_items` | Yes | Required for product-level sales, item counts, and revenue attribution. |
| `products` | Yes | Required for product dimension analysis (categories, attributes). |
| `sellers` | Yes | Required for seller performance metrics. |
| `order_payments` | Yes | Required to analyze payment methods and reconcile total order value. |
| `order_reviews` | Yes | Required to analyze customer experience and review scores. |
| `product_category_name_translation` | Yes | Required to translate Portuguese category names into English. |
| `geolocation` | **No** | Contains >1M rows with many duplicates; excluded to keep analytical focus sharp. Retained in `data/raw/` for potential future geographic extensions. |

---

## 2. Table Details & Grain

### 2.1. `orders`
- **Purpose**: Tracks order status and delivery timestamps.
- **Grain**: 1 row per distinct order event.
- **Primary Key (PK)**: `order_id`
- **Foreign Keys (FK)**: `customer_id` -> `customers.customer_id`
- **Important Columns**: `order_status`, `order_purchase_timestamp`, `order_delivered_customer_date`
- **Business Questions Supported**: How many orders were placed? What is the order status breakdown? How long does delivery take?
- **Data-Quality Checks**: Check for missing delivery dates on delivered orders; validate chronological order of timestamps.

### 2.2. `customers`
- **Purpose**: Stores customer location and identity. 
- **Grain**: 1 row per order's customer record (`customer_id`). *(Note: `customer_unique_id` identifies repeat individuals across multiple `customer_id` records).*
- **Primary Key (PK)**: `customer_id`
- **Important Columns**: `customer_unique_id`, `customer_city`, `customer_state`, `customer_zip_code_prefix`
- **Business Questions Supported**: Where do our customers live? How many repeat customers do we have?
- **Data-Quality Checks**: Check uniqueness of `customer_id`.

### 2.3. `order_items`
- **Purpose**: Stores individual items purchased within an order.
- **Grain**: 1 row per product item in an order.
- **Primary Key (PK)**: `order_id`, `order_item_id` (Composite)
- **Foreign Keys (FK)**: 
  - `order_id` -> `orders.order_id`
  - `product_id` -> `products.product_id`
  - `seller_id` -> `sellers.seller_id`
- **Important Columns**: `price`, `freight_value`
- **Business Questions Supported**: What are our best-selling products? How much revenue is generated per item?
- **Data-Quality Checks**: Ensure prices and freight values are >= 0. Ensure no orphaned items without a parent order.

### 2.4. `order_payments`
- **Purpose**: Stores payment methods and values for orders.
- **Grain**: 1 row per payment sequence/method per order.
- **Primary Key (PK)**: `order_id`, `payment_sequential` (Composite)
- **Foreign Keys (FK)**: `order_id` -> `orders.order_id`
- **Important Columns**: `payment_type`, `payment_value`, `payment_installments`
- **Business Questions Supported**: What payment methods are most popular? How often are installments used?
- **Data-Quality Checks**: Reconcile total `payment_value` per `order_id` against the sum of `price` + `freight_value` in `order_items`.

### 2.5. `order_reviews`
- **Purpose**: Stores customer feedback scores and comments.
- **Grain**: 1 row per review per order.
- **Primary Key (PK)**: `review_id`, `order_id` (Composite)
- **Foreign Keys (FK)**: `order_id` -> `orders.order_id`
- **Important Columns**: `review_score`, `review_creation_date`
- **Business Questions Supported**: What is the average review score? Are reviews correlated with delivery times?
- **Data-Quality Checks**: Ensure `review_score` is between 1 and 5. (Missing titles/comments are ignored as expected sparsity).

### 2.6. `products`
- **Purpose**: Stores product attributes and categorization.
- **Grain**: 1 row per distinct product.
- **Primary Key (PK)**: `product_id`
- **Foreign Keys (FK)**: `product_category_name` -> `product_category_name_translation.product_category_name`
- **Important Columns**: `product_category_name`, physical dimensions
- **Business Questions Supported**: Which product categories drive the most revenue?
- **Data-Quality Checks**: Check for missing category names (will be mapped to "Unknown" in Analytics).

### 2.7. `sellers`
- **Purpose**: Stores seller location information.
- **Grain**: 1 row per distinct seller.
- **Primary Key (PK)**: `seller_id`
- **Important Columns**: `seller_city`, `seller_state`
- **Business Questions Supported**: Where are our top-performing sellers located?

### 2.8. `product_category_name_translation`
- **Purpose**: Translates Portuguese product categories to English.
- **Grain**: 1 row per category name.
- **Primary Key (PK)**: `product_category_name`
- **Important Columns**: `product_category_name_english`

---

## 3. Relationships & Cardinality

| Source Table | Relationship | Target Table | Join Key |
| :--- | :---: | :--- | :--- |
| `orders` | 1 to 1 | `customers` | `customer_id` |
| `orders` | 1 to Many | `order_items` | `order_id` |
| `orders` | 1 to Many | `order_payments` | `order_id` |
| `orders` | 1 to Many | `order_reviews` | `order_id` |
| `order_items` | Many to 1 | `products` | `product_id` |
| `order_items` | Many to 1 | `sellers` | `seller_id` |
| `products` | Many to 1 | `product_category_name_translation` | `product_category_name` |

---

## 4. Join / Double-Counting Risks

### The "Cartesian Fan-Out" Risk
A major risk in analytical pipelines is joining multiple "one-to-many" child tables directly to a parent table in a single SQL query. 

**Example Risk:**
An order (`order_id`) has **3 items** (`order_items`) and the customer paid with **2 different payment methods** (`order_payments` - e.g., a voucher and a credit card). 
If we execute:
```sql
SELECT ...
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN order_payments op ON o.order_id = op.order_id
```
The resulting dataset will produce **3 × 2 = 6 rows** for this single order. 
- Summing `oi.price` on this joined result will double-count the item revenue.
- Summing `op.payment_value` on this joined result will triple-count the payment value.

### Mitigation Strategy for the Analytical Model
To prevent double-counting, the PostgreSQL analytical layer and KPI SQL will implement one of two strategies:

1. **Pre-Aggregation (CTEs/Subqueries):** Aggregate child tables to the `order_id` grain *before* joining them to the `orders` table. 
   - E.g., Calculate `Total Order Item Value` per order in one CTE, calculate `Total Payment Value` per order in another CTE, and then join both 1:1 to the `orders` table.
2. **Isolated Fact Tables:** Serve independent analytical views to Power BI. 
   - E.g., A `Sales by Item` view (grain: order item) and a `Payments` view (grain: payment line). They remain disconnected in Power BI to prevent cartesian explosions.
