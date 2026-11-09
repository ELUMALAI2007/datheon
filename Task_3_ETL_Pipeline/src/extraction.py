# ==============================================================================
# DATHEON INTERNSHIP - TASK 3
# EXTRACTION MODULE (INTELLIGENT CACHE-FIRST / LIVE SCRAPE)
# ==============================================================================

import logging
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from config import (
    MAX_RECORDS_TARGET,
    RAW_CSV_PATH,
    RAW_JSON_PATH,
    REQUEST_TIMEOUT_SECONDS,
    SCRAPER_URL,
    USER_AGENT,
)
from src.validation import validate_raw_data

logger = logging.getLogger("DatheonETLPipeline")


def create_resilient_session() -> requests.Session:
    """Create a requests session with automatic retries on network failures."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    retry_strategy = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def scrape_from_web() -> pd.DataFrame:
    """
    Scrape books live from books.toscrape.com with pagination, deduplication,
    and safe element parsing.
    """
    logger.info(f"Initiating resilient web extraction from: {SCRAPER_URL}")
    session = create_resilient_session()

    all_books = []
    seen_urls = set()
    current_url = SCRAPER_URL
    page_number = 1

    start_time = time.time()

    while current_url and len(all_books) < MAX_RECORDS_TARGET:
        logger.info(f"Scraping Page {page_number} ({current_url})...")
        try:
            response = session.get(current_url, timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code} received from {current_url}")
                break

            soup = BeautifulSoup(response.content, "html.parser")
            book_cards = soup.find_all("article", class_="product_pod")

            if not book_cards:
                logger.warning(f"No book elements found on Page {page_number}.")
                break

            for card in book_cards:
                # Safe title extraction
                title = card.h3.a.get("title") or card.h3.a.get_text(strip=True) if card.h3 and card.h3.a else None
                if not title:
                    continue

                # Safe price extraction
                price_tag = card.find("p", class_="price_color")
                price = price_tag.get_text(strip=True) if price_tag else None
                if not price:
                    continue

                # Safe rating extraction
                rating_tag = card.find("p", class_="star-rating")
                rating = rating_tag["class"][1] if rating_tag and len(rating_tag.get("class", [])) > 1 else "Unknown"

                # Safe availability extraction
                avail_tag = card.find("p", class_="instock availability")
                availability = avail_tag.get_text(strip=True) if avail_tag else "Unknown"

                # Safe URL extraction
                rel_url = card.h3.a.get("href", "") if card.h3 and card.h3.a else ""
                product_url = urljoin(current_url, rel_url)
                if not product_url or product_url in seen_urls:
                    continue

                seen_urls.add(product_url)
                all_books.append({
                    "Title": title.strip(),
                    "Price": price.strip(),
                    "Rating": rating.strip(),
                    "Availability": availability.strip(),
                    "URL": product_url.strip(),
                    "Page": page_number
                })

                if len(all_books) >= MAX_RECORDS_TARGET:
                    break

            # Handle pagination
            next_btn = soup.select_one("li.next a")
            if next_btn and len(all_books) < MAX_RECORDS_TARGET:
                current_url = urljoin(current_url, next_btn["href"])
                page_number += 1
            else:
                current_url = None

        except requests.RequestException as e:
            logger.error(f"Network error on Page {page_number}: {e}")
            break
        except Exception as e:
            logger.error(f"Parsing error on Page {page_number}: {e}")
            break

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Scraping finished in {elapsed}s. Total records collected: {len(all_books)}")

    df = pd.DataFrame(all_books)
    return df


def extract_data(force_scrape: bool = False) -> pd.DataFrame:
    """
    Main extraction entry point.
    Implements intelligent extraction: reuses cached raw data if valid,
    or triggers live scraping when requested or when cache is missing.
    """
    logger.info("==========================================")
    logger.info("STAGE 1: DATA EXTRACTION (E)")
    logger.info("==========================================")

    if not force_scrape and RAW_CSV_PATH.exists():
        logger.info(f"Existing raw data found at '{RAW_CSV_PATH}'. Loading from cache to avoid redundant network calls.")
        df = pd.read_csv(RAW_CSV_PATH)
        is_valid, _ = validate_raw_data(df)
        if is_valid and len(df) >= MAX_RECORDS_TARGET:
            logger.info(f"Extraction successful: {len(df)} records loaded from cache.")
            return df
        else:
            logger.warning("Cached raw data is incomplete or invalid. Falling back to live scrape.")

    # Live scrape
    df = scrape_from_web()
    is_valid, msg = validate_raw_data(df)
    if not is_valid:
        raise ValueError(f"Extraction stage failed validation: {msg}")

    # Persist raw files (Bronze Layer)
    df.to_csv(RAW_CSV_PATH, index=False, encoding="utf-8-sig")
    df.to_json(RAW_JSON_PATH, orient="records", indent=4, force_ascii=False)
    logger.info(f"Raw data cached to {RAW_CSV_PATH.name} and {RAW_JSON_PATH.name}")

    return df
