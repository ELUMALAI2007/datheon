# Datheon Technologies Internship: Python for Data Engineering & Automation

**Internship Application ID:** `DT-2026-245CV`  
**Track:** Python for Data Engineering & Automation  
**Author:** Third-Year B.Tech AI & Data Science  
**Operating Environment:** Windows 11 &bull; Python 3.13.5 &bull; VS Code &bull; PowerShell  
**GitHub Repository:** [https://github.com/ELUMALAI2007/datheon](https://github.com/ELUMALAI2007/datheon)  

---

## 📌 Executive Summary
This repository contains the complete, production-grade implementation of all three selected internship tasks for **Datheon Technologies**:

1. **TASK 1 – Autonomous Web Scraper & Data Extractor**: Resilient web scraper with exponential backoff retries, safe HTML element parsing, URL deduplication, and an interactive Flask Web Dashboard with live search and Chart.js visualizations.
2. **TASK 2 – Automated Data Cleaning & Schema Transformation**: Comprehensive data quality engine, schema validation, type conversions, missing-value and duplicate auditing before/after cleaning, feature engineering, and 4 publication-quality Matplotlib charts.
3. **TASK 3 – Relational Database Auto-Ingestion & Upsert Engine**: Modular Medallion ETL pipeline (Bronze ➔ Silver ➔ Gold Layer) powered by an explicit SQLite UPSERT engine (`INSERT ... ON CONFLICT(url) DO UPDATE`), ACID transaction safety with rollback on failure, `PRAGMA integrity_check`, and an 11-test automated Pytest suite.

---

## 🏛️ System Architecture

```
                                [ Books to Scrape Website ]
                                             │
                                             ▼  (HTTP Session / Auto-Retries / Safe Parsing)
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TASK 1: AUTONOMOUS WEB SCRAPER & INTERACTIVE DASHBOARD                                      │
│ - Pagination across 5 pages with exponential backoff retries (HTTP 429/5xx)                 │
│ - URL Deduplication (seen_urls set) & graceful handling of missing HTML elements            │
│ - Outputs: data/scraped_data.csv & scraped_data.json (100 book records)                     │
│ - Audit Report: scraping_report.txt                                                         │
│ - Interactive UI: Flask + Bootstrap 5 + Chart.js dashboard (app.py)                         │
└────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                             │
                                             ▼  (Input Dataset)
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TASK 2: DATA CLEANING, SCHEMA TRANSFORMATION & AUDIT                                        │
│ - Schema validation against required columns & expected data types                          │
│ - Missing value and duplicate audit before and after cleaning                               │
│ - Price numeric conversion & validation (£ symbol stripped, invalid prices dropped)        │
│ - Rating score mapping (1 to 5) & availability boolean flag engineering                     │
│ - Feature Engineering: Price Categories (Budget <£25, Mid-Range £25-£45, Premium >£45)      │
│ - Reports: data_quality_report.txt & validation_report.json                                 │
│ - Visualizations: 4 publication-grade Matplotlib charts saved to charts/                    │
└────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                             │
                                             ▼  (Modular Automation)
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TASK 3: AUTOMATED PRODUCTION ETL PIPELINE & SQLITE UPSERT ENGINE                            │
│ - Bronze Layer: src/extraction.py (Cache-first intelligent extraction + live scrape fallback)│
│ - Silver Layer: src/transformation.py (Cleaned business features & validation engine)      │
│ - Gold Layer  : src/loading.py (SQLite books.db with explicit UPSERT ON CONFLICT(url))      │
│ - Transaction Safety: Explicit COMMIT and automatic ROLLBACK on failure                     │
│ - Integrity Checks: PRAGMA integrity_check & Primary Key uniqueness verification            │
│ - Reports: database_report.txt & database_verification.json                                 │
│ - Orchestrator: run_pipeline.py (CLI entry point, centralized logging, summary metrics)     │
│ - Automated Tests: tests/test_pipeline.py (11/11 Pytest tests PASSED)                       │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Directory Structure

```
Datheon_Internship/
│
├── README.md                           # Master Portfolio Documentation
├── .gitignore                          # Clean production Git exclusions
│
├── Task_1_Web_Scraping/
│   ├── scraper.py                      # Autonomous web scraper with retries & logging
│   ├── app.py                          # Flask web dashboard application
│   ├── templates/index.html            # Responsive UI with Chart.js & instant search
│   ├── data/
│   │   ├── scraped_data.csv            # 100 clean book records
│   │   └── scraped_data.json           # JSON representation
│   ├── logs/scraper.log                # Scraping execution logs
│   ├── scraping_report.txt             # Scraping audit report
│   ├── requirements.txt                # requests, beautifulsoup4, pandas, flask
│   └── README.md                       # Task 1 documentation
│
├── Task_2_Data_Processing/
│   ├── data_processing.py              # Data quality audit, cleaning & visualization script
│   ├── data/
│   │   ├── scraped_data.csv            # Input dataset from Task 1
│   │   ├── cleaned_data.csv            # Cleaned & feature-engineered dataset
│   │   ├── analysis_summary.json       # Summary statistics in JSON
│   │   ├── rating_summary.csv          # GroupBy metrics by Star Rating
│   │   └── price_category_summary.csv  # GroupBy metrics by Price Category
│   ├── charts/                         # 4 Generated Matplotlib visualizations
│   │   ├── price_distribution.png
│   │   ├── rating_distribution.png
│   │   ├── avg_price_by_rating.png
│   │   └── price_category_share.png
│   ├── logs/data_processing.log        # Cleaning audit logs
│   ├── data_quality_report.txt         # Formal text data quality report
│   ├── validation_report.json          # Formal JSON validation report
│   ├── requirements.txt                # pandas, matplotlib
│   └── README.md                       # Task 2 documentation
│
└── Task_3_ETL_Pipeline/
    ├── run_pipeline.py                 # Master automated pipeline orchestrator
    ├── config.py                       # Centralized configuration
    ├── src/                            # Modular ETL engine
    │   ├── __init__.py                 # Package marker
    │   ├── logger_config.py            # Dual file/console logging
    │   ├── validation.py               # Schema & data constraint engine
    │   ├── extraction.py               # Cache-first / live scrape extraction
    │   ├── transformation.py           # Pandas cleaning, typing & feature engineering
    │   └── loading.py                  # Explicit SQLite UPSERT loader & verification
    ├── data/
    │   ├── raw/ (Bronze Layer)         # books_raw.csv & books_raw.json
    │   └── processed/ (Silver Layer)   # books_transformed.csv & books_transformed.json
    ├── database/books.db               # Gold Layer SQLite database (table 'books')
    ├── logs/pipeline.log               # Pipeline execution audit logs
    ├── tests/test_pipeline.py          # 11-scenario automated Pytest suite
    ├── database_report.txt             # Database audit report
    ├── database_verification.json      # Database verification metrics in JSON
    ├── requirements.txt                # requests, bs4, pandas, pytest
    └── README.md                       # Task 3 documentation
```

---

## 🛠️ Technology Stack
- **Core Language:** Python 3.13.5
- **Web Scraping & Resilience:** `requests`, `urllib3.util.Retry`, `HTTPAdapter`, `BeautifulSoup4`
- **Data Engineering & Analysis:** `pandas`, `numpy`
- **Database Engine:** `SQLite3`, `SQL` (Explicit UPSERT, Primary Keys, Indexes, Transactions)
- **Web Dashboard:** `Flask`, `Bootstrap 5`, `Chart.js`, `HTML5`, `CSS3`, `JavaScript`
- **Visualization:** `matplotlib`
- **Testing & Quality Assurance:** `pytest`, `unittest.mock`
- **Logging & System Utilities:** Python standard `logging`, `pathlib`, `argparse`

---

## 🚀 Step-by-Step Execution Guide

### 1. Task 1: Web Scraping & Dashboard
```powershell
cd Task_1_Web_Scraping
pip install -r requirements.txt

# Run autonomous scraper (collects 100 books, handles retries, writes scraping_report.txt)
python scraper.py

# Launch interactive Flask Web Dashboard
python app.py
# Open browser at: http://127.0.0.1:5000/
cd ..
```

### 2. Task 2: Data Cleaning, Quality Audit & Visualizations
```powershell
cd Task_2_Data_Processing
pip install -r requirements.txt

# Run data quality audit, schema validation, feature engineering, and chart generation
python data_processing.py
cd ..
```
*Generated Reports:*
- `Task_2_Data_Processing/data_quality_report.txt`
- `Task_2_Data_Processing/validation_report.json`
- `Task_2_Data_Processing/charts/*.png`

### 3. Task 3: Automated ETL Pipeline & Testing
```powershell
cd Task_3_ETL_Pipeline
pip install -r requirements.txt

# Run the complete automated ETL pipeline (with explicit SQLite UPSERT)
python run_pipeline.py

# Force live web re-scraping into the pipeline
python run_pipeline.py --scrape

# Execute the complete automated Pytest test suite (11 test scenarios)
python -m pytest tests -v
cd ..
```
*Generated Reports:*
- `Task_3_ETL_Pipeline/database_report.txt`
- `Task_3_ETL_Pipeline/database_verification.json`
- `Task_3_ETL_Pipeline/logs/pipeline.log`

---

## 📊 Summary of Final Verification & Results

### 1. Task 1: Autonomous Web Scraping
- **Status:** `SUCCESS` (100 Valid Records Extracted)
- **Duplicate URLs Prevented:** 0
- **Missing Elements Handled:** 0
- **Consistency:** CSV (100 rows) == JSON (100 records)
- **Report:** Verified in `Task_1_Web_Scraping/scraping_report.txt`

### 2. Task 2: Data Quality Audit
- **Status:** `PASSED`
- **Total Input Records:** 100 | **Total Clean Output Records:** 100
- **Schema Validation:** `PASSED` (All required columns present and typed)
- **Missing Values After Cleaning:** 0 across all columns (100% non-null)
- **Key Statistics:**
  - Average Price: £34.56
  - Median Price: £34.78
  - Price Range: £10.16 – £58.11
  - Average Rating: 2.93 / 5.0
- **Visualizations:** 4 charts generated in `Task_2_Data_Processing/charts/`

### 3. Task 3: SQLite UPSERT & Database Integrity
- **Status:** `PASSED`
- **UPSERT Engine:** `INSERT INTO books (...) ON CONFLICT(url) DO UPDATE SET ...`
- **PRAGMA integrity_check:** `ok`
- **Primary Key Uniqueness:** `PASSED` (Zero Duplicate URLs)
- **Total Records in SQLite:** 100
- **Idempotency:** Verified (Running pipeline multiple times preserves exactly 100 records)
- **ACID Safety:** Verified (Explicit `COMMIT` on success, `ROLLBACK` on exception)

### 4. Automated Testing Results
```text
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_web_scraper_extraction PASSED          [  9%]
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_network_failure_handling PASSED        [ 18%]
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_missing_html_elements_handling PASSED [ 27%]
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_data_cleaning PASSED                   [ 36%]
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_duplicate_removal PASSED                [ 45%]
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_schema_validation PASSED                [ 54%]
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_invalid_price_detection PASSED        [ 63%]
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_database_insertion PASSED               [ 72%]
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_database_upsert PASSED                 [ 81%]
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_transaction_rollback PASSED           [ 90%]
Task_3_ETL_Pipeline/tests/test_pipeline.py::test_pipeline_idempotency PASSED            [100%]

============================= 11 passed in 2.44s ==============================
```
