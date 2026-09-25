# Power BI Business Intelligence Dashboard

This document details the architecture and integration of the Power BI reporting layer for the Automated Business Reporting & Data Quality System.

## 1. Power BI Architecture & PostgreSQL Connection
Power BI acts strictly as the **Interactive Visualization and Business Intelligence layer**. It does not perform primary data transformations or core KPI calculations.

- **Connection:** Power BI connects directly to the local PostgreSQL database (`localhost:5432`, DB: `automated_business_reporting`) via Import mode.
- **Single Source of Truth:** PostgreSQL analytics views are the single source of truth for core business KPIs. Power BI is used primarily for interactive visualization and business analysis.

## 2. Analytics Views Used
The dashboard consumes the following eight, pre-aggregated analytical views from the `analytics` schema:
1. `v_order_kpis`
2. `v_monthly_sales`
3. `v_category_sales`
4. `v_payment_analysis`
5. `v_review_analysis`
6. `v_order_status`
7. `v_customer_analysis`
8. `v_data_quality_summary`

## 3. Grain & Fan-Out Prevention
Each view in the analytics schema was intentionally constructed in PostgreSQL to prevent data duplication (fan-out). 
- `v_order_kpis` is a grand total scalar.
- `v_monthly_sales` is at the Month grain.
- `v_category_sales` is at the Product Category grain.
- `v_payment_analysis` is at the Payment Type grain.

Because these grains differ, **these tables remain disconnected in the Power BI model**. Forcing them into a single relational schema inside Power BI would cause cartesian explosions when cross-filtering.

## 4. Page Structure & KPI Sourcing
The Power BI report is divided into 6 logical pages:
1. **Executive Overview**: High-level KPIs sourced directly from `v_order_kpis` (GMV, AOV, Total Orders, etc).
2. **Sales Performance**: Time-series trends sourced from `v_monthly_sales`.
3. **Product & Category Analysis**: Sourced from `v_category_sales`.
4. **Customer Analysis**: Lifetime value and repeat metrics sourced from `v_customer_analysis`.
5. **Payments & Reviews**: Financial distributions (`v_payment_analysis`) and customer sentiment (`v_review_analysis`).
6. **Data Quality**: Exposure of pipeline quarantine and validation results (`v_data_quality_summary`).

## 5. DAX Usage
DAX usage is heavily restricted. Because PostgreSQL acts as the metric calculation engine, Power BI relies on simple implicit aggregations (e.g., sum of `v_category_sales[gmv]`) rather than rebuilding complex calculations. No measure like `GMV = SUM(raw_order_items[price])` is permitted.

## 6. Currency Handling
The dataset represents Brazilian e-commerce operations. Financial figures are kept consistent with their source magnitudes and formatted cleanly as Currency ($/R$) without applying arbitrary conversion rates to other currencies (like INR) that would misrepresent the data.

## 7. Data-Quality Presentation
Data quality findings are exposed transparently on Page 6. This page confirms that missing product categories (handled as "Unknown") and timestamp anomalies were isolated and managed cleanly during the PostgreSQL ETL, allowing business users to trust the Executive KPIs.

## 8. Known Limitations & Refresh Considerations
- Without relationships, slicers act only on the specific visuals bound to their respective tables. 
- The dashboard requires the PostgreSQL service to be active during a data refresh.
