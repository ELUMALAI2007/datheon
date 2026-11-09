# Datheon Technologies Internship - Task 2: Data Processing & Analysis

**Application ID:** `DT-2026-245CV`  
**Internship Track:** Python for Data Engineering & Automation  
**Input Dataset:** `data/scraped_data.csv` (100 Books Scraped)  

---

## 📌 Project Overview
This project performs an in-depth **Exploratory Data Analysis (EDA)** and data transformation on the 100-record dataset generated from Task 1. Using **Pandas**, the data is inspected for missing values, deduplicated, cleaned, and enriched with business features (such as price tiers and availability flags). Comprehensive statistical summaries and GroupBy aggregations are computed, and publication-grade visualizations are generated using **Matplotlib**.

---

## 🏗️ Project Architecture
```
Task_2_Data_Processing/
│
├── data_processing.py               # Complete data processing & analysis script
├── requirements.txt                 # pandas, matplotlib
├── README.md                        # Documentation
│
├── data/
│   ├── scraped_data.csv             # Input dataset (from Task 1)
│   ├── cleaned_data.csv             # Transformed & feature-engineered dataset
│   ├── analysis_summary.json        # Comprehensive metrics in JSON format
│   ├── rating_summary.csv           # GroupBy metrics by Star Rating
│   └── price_category_summary.csv   # GroupBy metrics by Price Category
│
└── charts/                          # Generated Matplotlib charts
    ├── price_distribution.png       # Histogram with Mean Price line
    ├── rating_distribution.png      # Bar chart of rating counts
    ├── avg_price_by_rating.png      # Average price across star ratings
    └── price_category_share.png     # Donut chart of price tiers
```

---

## 📈 Key Statistical Findings

- **Total Books Analyzed:** 100
- **Average Price (Mean):** £34.56
- **Median Price:** £34.78
- **Price Range:** £10.16 to £58.11
- **Standard Deviation:** £14.64
- **Average Star Rating:** 2.93 / 5.0
- **Stock Availability:** 100% In Stock

### GroupBy Star Rating Summary
| Rating Score | Count | Average Price (£) | Min Price (£) | Max Price (£) |
| :---: | :---: | :---: | :---: | :---: |
| 1 Star | 22 | £35.52 | £12.84 | £56.41 |
| 2 Stars | 19 | £35.91 | £13.99 | £56.40 |
| 3 Stars | 22 | £36.84 | £10.16 | £57.31 |
| 4 Stars | 18 | £33.98 | £14.02 | £58.11 |
| 5 Stars | 19 | £30.01 | £13.34 | £54.23 |

### Price Tiers Breakdown
- **Budget (< £25):** 36 books (36%) &bull; Average Rating: 3.14
- **Mid-Range (£25 – £45):** 31 books (31%) &bull; Average Rating: 2.97
- **Premium (> £45):** 33 books (33%) &bull; Average Rating: 2.67

---

## 🚀 Execution Guide

1. Navigate to the Task 2 folder:
   ```powershell
   cd Task_2_Data_Processing
   ```

2. Run the processing and visualization pipeline:
   ```powershell
   python data_processing.py
   ```

All cleaned outputs will be written to `data/` and all visualizations will be saved to `charts/`.

