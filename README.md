# Datheon Technologies Internship: Python for Data Engineering & Automation

**Internship Application ID:** `DT-2026-245CV`  
**Track:** Python for Data Engineering & Automation  
**Student:** 3rd Year B.Tech Artificial Intelligence & Data Science  
**Operating Environment:** Windows 11 &bull; Python 3.13.5 &bull; VS Code &bull; PowerShell  

---

## 🎯 Executive Summary
This repository contains the complete, production-grade submissions for **Tasks 1, 2, and 3** of the Datheon Technologies Internship Program. All deliverables are built with modular, fault-tolerant Python architectures and connect into a unified Data Engineering lifecycle:

1. **Task 1 – Web Scraping & Portfolio Web Dashboard**: Multi-page web extraction with custom headers, session pooling, pagination, and an interactive Flask Web Dashboard with live filtering and Chart.js visualizations.
2. **Task 2 – Data Processing & Analysis with Pandas**: Comprehensive Exploratory Data Analysis (EDA), string wrangling, type conversions, feature engineering (Price Tiers, Availability flags), statistical GroupBy summaries, and Matplotlib chart generation.
3. **Task 3 – Automated Production ETL Pipeline**: Modular, automated Medallion ETL pipeline (Bronze ➔ Silver ➔ Gold), schema validation, idempotent upsert into SQLite relational database, centralized logging, and Pytest test suite.

---

## 🏛️ End-to-End System Architecture

```
                                  [ Books to Scrape Website ]
                                               │
                                               ▼  (Requests / BeautifulSoup)
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TASK 1: WEB SCRAPING & INTERACTIVE WEB DASHBOARD                                            │
│ - Multi-page pagination across 5 pages with error handling & User-Agent headers             │
│ - Outputs: data/scraped_data.csv & scraped_data.json (100 book records)                     │
│ - Portfolio Dashboard: Flask backend + Bootstrap 5 / Chart.js frontend (app.py)             │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼  (Clean Input Dataset)
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TASK 2: DATA PROCESSING & STATISTICAL ANALYSIS (PANDAS & MATPLOTLIB)                        │
│ - Null & duplicate auditing, currency symbol cleaning, rating mapping (1 to 5)              │
│ - Feature Engineering: Price Categories (Budget, Mid-Range, Premium), In_Stock booleans     │
│ - GroupBy Aggregations: Rating summaries, price tier summaries                              │
│ - Visualizations: 4 publication-quality charts saved to charts/                             │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼  (Modular Automation)
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TASK 3: AUTOMATED ETL PIPELINE (MEDALLION ARCHITECTURE & SQLITE)                            │
│ - Bronze Layer: src/extraction.py (Cache-first intelligent extraction)                      │
│ - Silver Layer: src/transformation.py (Cleaned & typed business features)                   │
│ - Gold Layer  : src/loading.py (SQLite database books.db with Primary Key & Indexes)        │
│ - Orchestrator: run_pipeline.py (CLI entry point, centralized logging, execution summary)   │
│ - Test Suite  : tests/test_pipeline.py (Automated Pytest unit & idempotency tests)          │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Directory Structure

```
Datheon_Internship/
│
├── Task_1_Web_Scraping/
│   ├── scraper.py                 # Main scraper & data cleaner
│   ├── app.py                     # Flask web dashboard application
│   ├── templates/index.html       # Responsive UI with Chart.js & instant search
│   ├── data/                      # 100-record CSV & JSON deliverables
│   ├── requirements.txt           # requests, bs4, pandas, flask
│   └── README.md                  # Task 1 documentation
│
├── Task_2_Data_Processing/
│   ├── data_processing.py         # Complete Pandas EDA & visualization script
│   ├── data/                      # Cleaned CSV & statistical JSON summaries
│   ├── charts/                    # Generated Matplotlib charts (.png)
│   ├── requirements.txt           # pandas, matplotlib
│   └── README.md                  # Task 2 documentation
│
├── Task_3_ETL_Pipeline/
│   ├── run_pipeline.py            # Master pipeline orchestrator
│   ├── config.py                  # Central configuration
│   ├── src/                       # Modular ETL components
│   │   ├── logger_config.py       # Dual-channel logging (file + console)
│   │   ├── validation.py          # Data validation & schema rules
│   │   ├── extraction.py          # Extract module (cache-first / live scrape)
│   │   ├── transformation.py      # Transform module (cleaning & feature eng.)
│   │   └── loading.py             # Load module (SQLite upsert & transactions)
│   ├── data/                      # Raw (Bronze) & Processed (Silver) data
│   ├── database/books.db          # Gold Layer: SQLite database table 'books'
│   ├── logs/pipeline.log          # Operational audit log
│   ├── tests/test_pipeline.py     # Pytest test suite (100% pass)
│   ├── requirements.txt           # requests, bs4, pandas, pytest
│   └── README.md                  # Task 3 documentation
│
├── .gitignore                     # Production Git ignore rules
└── README.md                      # Unified repository master guide
```

---

## 🚀 Step-by-Step Execution Guide

### Task 1: Web Scraping & Dashboard
```powershell
cd Task_1_Web_Scraping
pip install -r requirements.txt
python scraper.py     # Runs the scraper (extracts 100 books)
python app.py         # Starts dashboard at http://127.0.0.1:5000/
cd ..
```

### Task 2: Data Processing & Visualizations
```powershell
cd Task_2_Data_Processing
pip install -r requirements.txt
python data_processing.py  # Executes EDA, statistical summaries & generates charts/
cd ..
```

### Task 3: Automated ETL Pipeline & Testing
```powershell
cd Task_3_ETL_Pipeline
pip install -r requirements.txt
python run_pipeline.py     # Runs automated ETL pipeline end-to-end
python -m pytest tests -v  # Executes automated test suite (4/4 tests passed)
cd ..
```

---

## 🛠️ Technology Stack
- **Languages & Core:** Python 3.13.5
- **Web Scraping:** `requests`, `BeautifulSoup4`
- **Data Engineering & Analysis:** `pandas`, `numpy`
- **Database:** `SQLite3`, `SQL` (ACID transactions, primary keys, indexes)
- **Web Frontend & Dashboard:** `Flask`, `Bootstrap 5`, `Chart.js`, `HTML5`, `CSS3`, `JavaScript`
- **Data Visualization:** `matplotlib`
- **Logging & Testing:** `logging`, `pytest`

