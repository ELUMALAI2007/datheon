# Datheon Technologies Internship - Task 1: Web Scraping & Dashboard

**Application ID:** `DT-2026-245CV`  
**Internship Track:** Python for Data Engineering & Automation  
**Target Website:** [Books to Scrape](https://books.toscrape.com/)  

---

## 📌 Project Overview
This project extracts 100 structured book records from the Books to Scrape website across 5 paginated web pages using Python, `requests`, and `BeautifulSoup4`. The extracted data is cleaned, validated, and exported into both **CSV** and **JSON** formats. Additionally, an interactive **Flask Web Dashboard** is included to explore the dataset with KPI cards, dynamic Chart.js visualizations, and instant search/filtering.

---

## 🏗️ Project Architecture
```
Task_1_Web_Scraping/
│
├── scraper.py             # Main web scraper & cleaning script
├── app.py                 # Flask web dashboard application
├── requirements.txt       # Project dependencies
├── README.md              # Task documentation
│
├── data/
│   ├── scraped_data.csv   # Cleaned 100-record CSV export
│   └── scraped_data.json  # Cleaned 100-record JSON export
│
└── templates/
    └── index.html         # Responsive dashboard UI (Bootstrap 5 + Chart.js)
```

---

## 📊 Extracted Data Fields
| Field Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `Title` | String | Full title of the book | *A Light in the Attic* |
| `Price` | String | Raw price with currency symbol | *£51.77* |
| `Rating` | String | Star rating text | *Three* |
| `Availability` | String | Stock status | *In stock* |
| `URL` | String | Absolute URL to product detail page | *https://books.toscrape.com/...* |
| `Page` | Integer | Source page number | *1* |
| `Price_Value` | Float | Cleaned numeric price value | *51.77* |
| `Rating_Score` | Integer | Mapped numeric rating (1 to 5) | *3* |

---

## 🚀 Setup & Execution Guide

### 1. Install Dependencies
Open your PowerShell terminal and run:
```powershell
pip install -r requirements.txt
```

### 2. Run the Web Scraper
To extract, validate, and export the dataset:
```powershell
python scraper.py
```
**Expected Output:**
- Progress logs for Pages 1 through 5.
- Validation metrics (zero duplicates, zero missing essential fields).
- Cleaned CSV and JSON generated in the `data/` directory.

### 3. Launch the Web Dashboard
To start the local portfolio dashboard:
```powershell
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

**Dashboard Features:**
- **KPI Metrics:** Total Products, Average Price, Min/Max Price.
- **Charts:** Star Rating distribution (Doughnut) and Price Range breakdown (Bar).
- **Search & Filters:** Real-time client-side search by title and filter by star rating.
- **Data Export:** Direct one-click downloads for CSV and JSON.

---

## 🛡️ Error Handling & Data Quality
- **Network Resilience:** Uses `requests.Session()` with connection pooling, timeouts (15s), and User-Agent headers.
- **Pagination Safety:** Extracts the relative `li.next a` link and safely resolves it using `urllib.parse.urljoin`.
- **Duplicate Prevention:** Drops duplicate entries based on book `Title`.
- **Data Transformation:** Converts currency strings to float and textual ratings into integer scales.

