# Pipeline Automation

This document outlines the architecture, execution flow, and behavioral characteristics of the Automated Business Reporting & Data Quality System pipeline.

## Pipeline Architecture

The pipeline orchestrates several modular Python scripts to process raw CSV data into a validated, clean PostgreSQL data warehouse, and finally generates an Excel report. Power BI connects directly to the final `analytics` schema in the database for interactive dashboarding.

### Execution Order

1. **Ingestion (`load_staging.py`)**: Connects to the database (creates it if it doesn't exist), sets up schemas (`staging`, `clean`, `analytics`, `quality`), and loads raw CSV files from `data/raw/` into the `staging` schema using pandas and SQLAlchemy.
2. **Validation (`dq_checks.py`)**: Runs data quality rules against the `staging` tables and records the results in `quality.data_quality_results`. Generates a Markdown report in `reports/data_quality_report.md`.
3. **Cleaning & Transformation (`clean_data.py`)**: Reads from `staging`, applies business logic to clean data (e.g., handling nulls, standardizing types), isolates invalid records into `quality.invalid_records` (quarantine behavior), and creates the `clean` schema tables.
4. **Analytics (`create_views.py`)**: Creates predefined SQL views in the `analytics` schema. These views calculate key performance indicators (KPIs) and aggregations.
5. **Reporting (`create_excel_report.py`)**: Queries the `analytics` views and generates a formatted Excel report `automated_business_report.xlsx` in `reports/excel/`.
6. **Validation (Final Stage in `run_pipeline.py`)**: Asserts that the final generated KPI views match a set of validated, expected baseline metrics to ensure pipeline integrity.

## How Failures are Handled

- **Fail-Fast Mechanism**: The orchestration script `run_pipeline.py` wraps each module's execution in a `try-except` block. If any step fails (raises an exception or exits with a non-zero exit code), the pipeline stops immediately and returns a non-zero exit code.
- **Reporting**: When a failure occurs, the script prints an explicit `❌ ERROR:` message to standard output indicating which stage failed.

## Idempotency and Re-run Behavior

The pipeline is designed to be fully idempotent and safe to rerun at any time:
- The staging tables are loaded with `if_exists="replace"`.
- The data quality results table is truncated before each run.
- The clean tables and invalid records table are dropped/truncated and recreated.
- Analytics views are created using `CREATE OR REPLACE VIEW`.
- The final Excel report is overwritten on each run (`automated_business_report.xlsx`), and a new timestamped copy is added to the `archive/` directory.

## Output Files

- `reports/data_quality_report.md`: Markdown summary of validation checks on raw data.
- `reports/excel/automated_business_report.xlsx`: The final formatted Excel workbook containing KPIs and charts. Always represents the latest successful run.
- `reports/excel/archive/automated_business_report_YYYY-MM-DD_HH-MM-SS.xlsx`: A timestamped archive copy of the report, generated only after a completely successful pipeline execution.
## PostgreSQL Schemas Involved

- `staging`: Raw data directly ingested from CSVs.
- `quality`: Contains the results of the data quality checks and the quarantined invalid records.
- `clean`: Validated and cleansed data ready for modeling.
- `analytics`: Pre-aggregated SQL views calculating KPIs and trends.

## Power BI's Role

Power BI acts as the final consumption layer for interactive analytics. It bypasses the Python reporting layer and connects directly to the `analytics` schema in the PostgreSQL database. The data in these views is pre-aggregated and cleansed, ensuring that Power BI visualizations accurately reflect the validated business metrics without needing complex DAX transformations.

## Known Limitations

- The current pipeline loads data in-memory using Pandas before writing to PostgreSQL, which might not scale efficiently for extremely large datasets (e.g., gigabytes of data).
- Incremental loading is not supported; the pipeline performs a full truncate-and-load operation.
