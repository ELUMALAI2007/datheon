# Datheon Technologies Internship - Task 3: Automated ETL Pipeline

**Application ID:** `DT-2026-245CV`  
**Internship Track:** Python for Data Engineering & Automation  
**Target Architecture:** Modular Medallion Pipeline (Bronze ➔ Silver ➔ Gold Layer)  

---

## 📌 Project Overview
This project implements an automated, fault-tolerant **ETL (Extract, Transform, Load) Pipeline** using Python, Pandas, and SQLite. The pipeline ingests book data from Books to Scrape, enforces data quality validation rules, transforms messy text into structured numeric and categorical features, and loads records idempotently into a local relational database with full transaction safety and centralized audit logging.

---

## 🏗️ Pipeline Architecture
```
Task_3_ETL_Pipeline/
│
├── run_pipeline.py           # Master CLI orchestrator
├── config.py                 # Centralized configuration & constants
├── requirements.txt          # Dependencies (requests, bs4, pandas, pytest)
├── README.md                 # System documentation
│
├── src/                      # Modular ETL core
│   ├── logger_config.py      # Dual-destination logging (console + log file)
│   ├── validation.py         # Schema & constraint validation engine
│   ├── extraction.py         # Extract module (cache-first + live scraper)
│   ├── transformation.py     # Transform module (cleaning, typing, feature engineering)
│   └── loading.py            # Load module (SQLite upsert, indexes, transactions)
│
├── data/
│   ├── raw/                  # Bronze Layer: books_raw.csv & books_raw.json
│   └── processed/            # Silver Layer: books_transformed.csv & .json
│
├── database/                 # Gold Layer: SQLite database (books.db)
│   └── books.db
│
├── logs/                     # Operational audit trail
│   └── pipeline.log
│
└── tests/                    # Automated testing suite
    └── test_pipeline.py      # Pytest validation & idempotency tests
```

---

## ⚙️ ETL Execution Stages

### 1. Extract (E) – `src/extraction.py`
- Implements **cache-first intelligent extraction**: If valid raw data exists at `data/raw/books_raw.csv`, it avoids hammering the website.
- Supports `--scrape` flag to force a live multi-page extraction across `books.toscrape.com` with `requests.Session` and User-Agent headers.
- Emits raw Bronze-layer files: `books_raw.csv` and `books_raw.json`.

### 2. Transform (T) – `src/transformation.py`
- **String Cleaning**: Trims whitespace and normalizes text fields.
- **Deduplication**: Removes duplicate records based on unique product `URL`.
- **Type Conversions**:
  - `Price` ("£51.77") ➔ `Price_Value` (Float: 51.77)
  - `Rating` ("Three") ➔ `Rating_Score` (Integer: 3)
- **Feature Engineering**:
  - `In_Stock_Flag`: Boolean integer (1 for in stock, 0 otherwise).
  - `Price_Category`: Categorical bins (`Budget (<£25)`, `Mid-Range (£25-£45)`, `Premium (>£45)`).
- Emits clean Silver-layer files: `books_transformed.csv` and `books_transformed.json`.

### 3. Load (L) – `src/loading.py`
- Connects to SQLite database `database/books.db`.
- Creates table `books` with Primary Key `url` and performance indexes on `price_value` and `rating_score`.
- Employs **idempotent upsert** (`INSERT OR REPLACE INTO books`) ensuring rerun safety with zero duplicate rows.
- Full ACID transaction handling (`COMMIT` on success, `ROLLBACK` on error).

---

## 🚀 Execution & Testing Guide

### 1. Run the Pipeline (Default Cache-First)
```powershell
python run_pipeline.py
```

### 2. Force a Live Web Scrape & Ingestion
```powershell
python run_pipeline.py --scrape
```

### 3. Run Pytest Suite
```powershell
python -m pytest tests -v
```

---

## 📋 Sample Pipeline Execution Output
```text
==================================================
             ETL PIPELINE SUMMARY
==================================================
Extraction       : SUCCESS (100 records)
Transformation   : SUCCESS (100 records)
Loading (SQLite) : SUCCESS (100 records)
--------------------------------------------------
Records Extracted : 100
Records Processed : 100
Records Loaded    : 100
--------------------------------------------------
CSV Export       : SUCCESS (books_transformed.csv)
JSON Export      : SUCCESS (books_transformed.json)
Database Storage : SUCCESS (books.db -> table 'books')
--------------------------------------------------
Pipeline Status  : COMPLETED
Total Duration   : 0.11 seconds
==================================================
```

