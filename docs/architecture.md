# Pipeline Architecture

This document explains the end-to-end flow of the Automated Business Reporting & Data Quality System.

## Complete Flow

Raw CSV → Python/Pandas → PostgreSQL `staging` → PostgreSQL `quality` → PostgreSQL `clean` → PostgreSQL `analytics` → Excel & Power BI

### 1. Raw CSV
- **Source:** Brazilian E-Commerce Public Dataset by Olist (stored locally in `data/raw/`).
- **Responsibility:** Act as the immutable, raw origin of truth.

### 2. Python/Pandas (Ingestion)
- **Component:** `src/ingestion/load_staging.py`
- **Responsibility:** Connects to PostgreSQL, dynamically builds schemas, and uses `pandas.to_sql` to push CSV data directly into the database. Memory-based load is used as the dataset is sufficiently small for standard operations.

### 3. Staging Schema (`staging`)
- **Component:** PostgreSQL schema populated during ingestion.
- **Responsibility:** Holds an exact, unadulterated 1:1 copy of the CSV files inside PostgreSQL. No data types or missing values are altered here. It serves as the baseline for data quality validation.

### 4. Quality Schema (`quality`)
- **Component:** `src/validation/dq_checks.py` & PostgreSQL schema
- **Responsibility:** Stores the output of the data quality checks (`quality.data_quality_results`). It also holds the `quality.invalid_records` table where the cleansing layer isolates records that fail objective business rules (e.g., negative dimensions).

### 5. Clean Schema (`clean`)
- **Component:** `src/cleaning/clean_data.py`
- **Responsibility:** Contains the sanitized data model. Handles timestamp nullification, removes quarantined rows, standardizes types, and provides a stable, referentially intact schema for modeling. This protects downstream analytics from bad data while keeping legitimate rows.

### 6. Analytics Schema (`analytics`)
- **Component:** `src/analytics/create_views.py`
- **Responsibility:** Houses predefined, pre-aggregated SQL views calculating KPIs. Crucially, it manages fan-out protection. Because a single order can have multiple items, multiple payments, and multiple reviews, joining them all into a single flat table would cause revenue to multiply arbitrarily. The analytics layer pre-aggregates items, payments, and reviews separately before they meet in the final views.

### 7. Excel Reporting
- **Component:** `src/reporting/create_excel_report.py`
- **Responsibility:** Connects to the `analytics` views, applies formatting via `openpyxl`, generates executive charts, and outputs a highly readable `.xlsx` workbook. Designed for automated distribution and archival.

### 8. Power BI
- **Component:** Manual PBIX dashboard connected to PostgreSQL.
- **Responsibility:** Serves as the interactive BI consumption layer. It connects directly to the pre-calculated `analytics` views rather than the raw tables, bypassing the need for complex DAX logic and ensuring the dashboard perfectly matches the Python/Postgres validated baselines. It must be manually or schedule refreshed after the Python orchestrator updates the database.
