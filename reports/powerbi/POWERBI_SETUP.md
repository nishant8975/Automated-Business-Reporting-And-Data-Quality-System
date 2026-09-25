# Power BI Setup Guide

Since automated generation of `.pbix` files is not natively supported by the agent environment, this document serves as the exact specification to manually build the Power BI dashboard for the Automated Business Reporting project.

## 1. Connection & Import Instructions

1. Open Power BI Desktop.
2. Go to **Get Data** > **PostgreSQL database**.
3. **Server:** `localhost:5432`
4. **Database:** `automated_business_reporting`
5. **Data Connectivity Mode:** Import
6. **Authentication:** Enter the database username and password configured in your local `.env` file. (Do NOT save or commit these credentials).
7. In the Navigator, expand the `analytics` schema and select the following 8 views:
   - `v_order_kpis`
   - `v_monthly_sales`
   - `v_category_sales`
   - `v_payment_analysis`
   - `v_review_analysis`
   - `v_order_status`
   - `v_customer_analysis`
   - `v_data_quality_summary`
8. Click **Load**.

## 2. Model Configuration

- **Relationships:** Because these views are already pre-aggregated to specific grains in PostgreSQL, do NOT create relationships between them. Doing so risks cartesian explosions (fan-out) and invalid KPI calculations. Leave them as disconnected tables in the Power BI Model View.
- **Formatting:** Ensure all monetary columns (e.g., `gmv`, `total_freight`, `merchandise_plus_freight`, `aov`, `total_payment_value`) are formatted as Currency ($). Ensure percentage columns are formatted as Percentages.
- **DAX:** No complex DAX measures are needed. Simply drag and drop the pre-calculated fields into your visuals. The only DAX permitted are basic UI helpers (e.g., dynamic titles) if strictly necessary.

## 3. Page-by-Page Visual Specification

### PAGE 1 — Executive Overview
**Purpose:** Quick view of overall performance.
- **KPI Cards (Source: `v_order_kpis`):** 
  - Total Orders (99,441)
  - Total Customers (96,096)
  - Repeat Customers (2,997)
  - GMV ($13,591,643.70)
  - AOV ($136.68)
  - Total Items (112,650)
  - Total Freight ($2,251,909.54)
  - Average Review Score (4.09)
- **Visuals:**
  - *Monthly GMV Trend:* Line chart using `v_monthly_sales` (`order_month` on X-axis, `gmv` on Y-axis).
  - *Monthly Orders Trend:* Column chart using `v_monthly_sales` (`order_month` on X-axis, `total_orders` on Y-axis).
  - *Top Product Categories by GMV:* Bar chart using `v_category_sales` (Top 5-10 by `gmv`).
  - *Order Status Distribution:* Donut chart using `v_order_status` (`order_status` as legend, `total_orders` as values).

### PAGE 2 — Sales Performance
**Purpose:** Deep dive into monthly trends.
**Source:** `v_monthly_sales`
- **Visuals:**
  - *GMV by Month:* Line chart (`order_month` vs `gmv`).
  - *Orders by Month:* Column chart (`order_month` vs `total_orders`).
  - *AOV by Month:* Line chart (`order_month` vs `aov`).
  - *Monthly GMV and Freight:* Stacked column chart comparing `gmv` and `total_freight`.
- **Table:** A matrix or table visual showing Month, Orders, GMV, Freight, Merchandise + Freight, and AOV.

### PAGE 3 — Product & Category Analysis
**Purpose:** Performance across the product catalog.
**Source:** `v_category_sales`
- **Visuals:**
  - *GMV by Category:* Bar chart.
  - *Orders by Category:* Bar chart.
  - *Items by Category:* Column chart.
- **Table:** Category, GMV, Orders, Items, Freight. Sort by GMV descending.
*(Note: Do NOT filter out the "Unknown" category.)*

### PAGE 4 — Customer Analysis
**Purpose:** Customer behavior and lifetime value.
**Source:** `v_customer_analysis`
- **Visuals:**
  - *One-Time vs Repeat Customers:* Donut chart (`customer_type` vs Count of `customer_unique_id`).
  - *Customer Order Frequency:* Bar chart grouping users by `total_orders`.
  - *Customer GMV Distribution:* Histogram or bar chart of `total_gmv` buckets.
- **Table:** Top Customers by GMV (Limit to top 100 for performance).

### PAGE 5 — Payments & Reviews
**Purpose:** Understand payment methods and customer satisfaction.
- **PAYMENTS Section (Source: `v_payment_analysis`):**
  - *Payment Value by Payment Type:* Bar chart (Ensure it is labeled "Total Payment Value", NOT "Revenue" or "GMV").
  - *Orders by Payment Type:* Column chart.
- **REVIEWS Section (Source: `v_review_analysis`):**
  - *Review Score Distribution:* Column chart (`review_score` vs `review_count`).
  - *Average Review Score:* KPI Card (Source: `v_order_kpis.average_review_score`).

### PAGE 6 — Data Quality
**Purpose:** Expose pipeline quality metrics.
**Source:** `v_data_quality_summary`
- **Visuals:**
  - KPI Cards for: Total Invalid Records, Invalid Product Records, Invalid Payment Records, Orders with Timestamp Anomalies, Products with Missing Category.
- **Text Box:** "Data quality validation and cleaning were performed in the Python/PostgreSQL processing layer. Power BI presents the resulting validated quality indicators."

## 4. Validation Checklist
Before publishing or distributing the report, verify the following baseline figures against the visuals:
- [ ] Executive GMV is exactly $13,591,643.70
- [ ] Executive Orders is exactly 99,441
- [ ] Executive Customers is exactly 96,096
- [ ] Category GMV total matches Executive GMV
- [ ] Monthly GMV total matches Executive GMV
- [ ] Total Payment Value is exactly $16,008,683.49 (This is intentionally different from GMV)
- [ ] No visuals display "(Blank)" unexpectedly. "Unknown" is perfectly valid for missing categories.
- [ ] No fan-out or inflated values exist.
