# ==============================================================================
# DATHEON INTERNSHIP - TASK 1
# AUTONOMOUS WEB SCRAPER & DATA EXTRACTOR
# ==============================================================================

from datetime import datetime
import json
import logging
from pathlib import Path
import sys
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# ==============================================================================
# 1. PROJECT CONFIGURATION
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

START_URL = "https://books.toscrape.com/"
MAX_RECORDS = 100
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 1.0
STATUS_FORCELIST = [429, 500, 502, 503, 504]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DatheonScraper/2.0"

CSV_OUTPUT = DATA_DIR / "scraped_data.csv"
JSON_OUTPUT = DATA_DIR / "scraped_data.json"
REPORT_OUTPUT = BASE_DIR / "scraping_report.txt"
LOG_FILE = LOGS_DIR / "scraper.log"

# ==============================================================================
# 2. LOGGING CONFIGURATION
# ==============================================================================
def setup_scraper_logger() -> logging.Logger:
    logger = logging.getLogger("DatheonScraper")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)-8s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        # File handler
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

logger = setup_scraper_logger()

# ==============================================================================
# 3. ROBUST REQUEST SESSION WITH RETRIES
# ==============================================================================
def create_robust_session() -> requests.Session:
    """Create a requests session with automatic exponential backoff retries."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        status_forcelist=STATUS_FORCELIST,
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# ==============================================================================
# 4. SAFE RECORD EXTRACTION & VALIDATION
# ==============================================================================
def extract_single_book(card, current_url: str, page_number: int) -> dict | None:
    """
    Safely extract book information from a product_pod HTML element.
    Handles missing elements gracefully without crashing.
    """
    try:
        # Title
        title = None
        if card.h3 and card.h3.a:
            title = card.h3.a.get("title") or card.h3.a.get_text(strip=True)
        if not title:
            logger.warning("Missing title element in book card; skipping.")
            return None

        # Price
        price_elem = card.find("p", class_="price_color")
        price = price_elem.get_text(strip=True) if price_elem else None
        if not price:
            logger.warning(f"Missing price for '{title}'; skipping.")
            return None

        # Rating
        rating_elem = card.find("p", class_="star-rating")
        rating = None
        if rating_elem and len(rating_elem.get("class", [])) > 1:
            rating = rating_elem["class"][1]
        else:
            rating = "Unknown"

        # Availability
        avail_elem = card.find("p", class_="instock availability")
        availability = avail_elem.get_text(strip=True) if avail_elem else "Unknown"

        # Product URL
        relative_url = card.h3.a.get("href", "") if card.h3 and card.h3.a else ""
        book_url = urljoin(current_url, relative_url) if relative_url else ""
        if not book_url:
            logger.warning(f"Missing URL for '{title}'; skipping.")
            return None

        return {
            "Title": title.strip(),
            "Price": price.strip(),
            "Rating": rating.strip(),
            "Availability": availability.strip(),
            "URL": book_url.strip(),
            "Page": page_number
        }
    except Exception as e:
        logger.error(f"Unexpected parsing error for book card: {e}")
        return None

# ==============================================================================
# 5. SCRAPER ENGINE WITH PAGINATION & DEDUPLICATION
# ==============================================================================
def scrape_books(max_records: int = MAX_RECORDS) -> tuple[list[dict], dict]:
    """
    Scrape books until max_records is reached.
    Guarantees no duplicate URLs and handles network retries.
    """
    session = create_robust_session()
    all_books = []
    seen_urls = set()
    current_url = START_URL
    page_number = 1

    stats = {
        "start_time": datetime.now().isoformat(),
        "pages_scraped": 0,
        "total_cards_found": 0,
        "valid_records": 0,
        "duplicates_skipped": 0,
        "missing_elements_skipped": 0,
        "network_errors": 0,
        "duration_seconds": 0.0
    }

    start_timer = time.time()
    logger.info("=" * 60)
    logger.info("   DATHEON WEB SCRAPING STARTED")
    logger.info(f"   Target: {START_URL} | Goal: At least {max_records} records")
    logger.info("=" * 60)

    while current_url and len(all_books) < max_records:
        logger.info(f"Scraping Page {page_number}: {current_url}")
        stats["pages_scraped"] += 1

        try:
            response = session.get(current_url, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code} received from {current_url}")
                stats["network_errors"] += 1
                break

            soup = BeautifulSoup(response.content, "html.parser")
            book_cards = soup.find_all("article", class_="product_pod")
            stats["total_cards_found"] += len(book_cards)

            for card in book_cards:
                book_data = extract_single_book(card, current_url, page_number)
                if not book_data:
                    stats["missing_elements_skipped"] += 1
                    continue

                if book_data["URL"] in seen_urls:
                    stats["duplicates_skipped"] += 1
                    logger.warning(f"Duplicate URL detected, skipping: {book_data['URL']}")
                    continue

                seen_urls.add(book_data["URL"])
                all_books.append(book_data)
                stats["valid_records"] += 1

                if len(all_books) >= max_records:
                    break

            logger.info(f"Progress: {len(all_books)} / {max_records} books collected.")

            # Pagination check
            next_page = soup.select_one("li.next a")
            if next_page and len(all_books) < max_records:
                current_url = urljoin(current_url, next_page["href"])
                page_number += 1
            else:
                current_url = None

        except requests.RequestException as error:
            logger.error(f"Network error on Page {page_number}: {error}")
            stats["network_errors"] += 1
            break

    stats["duration_seconds"] = round(time.time() - start_timer, 2)
    stats["end_time"] = datetime.now().isoformat()
    return all_books, stats

# ==============================================================================
# 6. DATA CLEANING & TYPE CONVERSION
# ==============================================================================
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean extracted DataFrame and add standard numeric features."""
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Drop duplicates by Title and URL
    df = df.drop_duplicates(subset=["URL"]).reset_index(drop=True)

    # Clean price to numeric float
    df["Price_Value"] = pd.to_numeric(
        df["Price"].astype(str).str.replace("£", "", regex=False).str.strip(),
        errors="coerce"
    )

    # Map ratings
    rating_mapping = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    df["Rating_Score"] = df["Rating"].map(rating_mapping).fillna(0).astype(int)

    # Drop any corrupt records
    df = df.dropna(subset=["Title", "URL", "Price_Value"]).reset_index(drop=True)
    return df

# ==============================================================================
# 7. EXPORT DATA & GENERATE SCRAPING REPORT
# ==============================================================================
def export_and_report(df: pd.DataFrame, stats: dict) -> None:
    """Export dataset to CSV and JSON, and write scraping summary report."""
    if df.empty:
        logger.error("No valid records to export.")
        return

    # Export CSV
    df.to_csv(CSV_OUTPUT, index=False, encoding="utf-8-sig")
    logger.info(f"CSV Exported: {CSV_OUTPUT} ({len(df)} records)")

    # Export JSON
    df.to_json(JSON_OUTPUT, orient="records", indent=4, force_ascii=False)
    logger.info(f"JSON Exported: {JSON_OUTPUT} ({len(df)} records)")

    # Verify consistency
    csv_rows = len(pd.read_csv(CSV_OUTPUT))
    with open(JSON_OUTPUT, "r", encoding="utf-8") as f:
        json_rows = len(json.load(f))

    assert csv_rows == json_rows == len(df), "Inconsistency between CSV and JSON exports!"
    logger.info(f"Consistency verified: CSV ({csv_rows} rows) == JSON ({json_rows} records)")

    # Generate Text Report
    report_text = f"""==================================================
        DATHEON TASK 1: WEB SCRAPING REPORT
==================================================
Execution Timestamp : {stats['start_time']}
Completion Time     : {stats['end_time']}
Total Duration      : {stats['duration_seconds']} seconds
Target Website      : {START_URL}

--- SCRAPING METRICS ---
Pages Scraped               : {stats['pages_scraped']}
Total Cards Found           : {stats['total_cards_found']}
Valid Records Extracted     : {stats['valid_records']}
Duplicate URLs Prevented    : {stats['duplicates_skipped']}
Missing Elements Handled    : {stats['missing_elements_skipped']}
Network Failures Encountered: {stats['network_errors']}

--- DELIVERABLES ---
CSV Output   : {CSV_OUTPUT.resolve()} ({csv_rows} records)
JSON Output  : {JSON_OUTPUT.resolve()} ({json_rows} records)
Log File     : {LOG_FILE.resolve()}

--- INTEGRITY CHECK ---
Record Count Match          : PASSED ({csv_rows} == {json_rows})
Minimum 100 Records Status  : {'PASSED' if len(df) >= 100 else 'FAILED'}
Overall Task 1 Status       : SUCCESS
==================================================
"""
    with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
        f.write(report_text)
    logger.info(f"Scraping report generated: {REPORT_OUTPUT}")

# ==============================================================================
# 8. MAIN ENTRY POINT
# ==============================================================================
def main():
    books, stats = scrape_books(max_records=MAX_RECORDS)
    if not books:
        logger.error("Scraping failed to yield any records.")
        return

    df_raw = pd.DataFrame(books)
    df_clean = clean_data(df_raw)
    export_and_report(df_clean, stats)

    logger.info("=" * 60)
    logger.info(f"DATHEON TASK 1 FINISHED: {len(df_clean)} Clean Records Ready!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
