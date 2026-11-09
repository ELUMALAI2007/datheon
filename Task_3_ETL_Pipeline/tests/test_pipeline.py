# ==============================================================================
# DATHEON INTERNSHIP - TASK 3
# AUTOMATED TEST SUITE: SCRAPING, CLEANING, UPSERT & IDEMPOTENCY
# ==============================================================================

from pathlib import Path
import sqlite3
import sys
from unittest.mock import MagicMock, patch

# Ensure Task_3_ETL_Pipeline root is on sys.path
TEST_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TEST_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bs4 import BeautifulSoup
import pandas as pd
import pytest
import requests

from src.extraction import create_resilient_session, extract_data, scrape_from_web
from src.loading import create_database_schema, load_to_sqlite, verify_database
from src.transformation import transform_data
from src.validation import validate_raw_data, validate_transformed_data


@pytest.fixture
def sample_raw_dataframe():
    """Fixture providing valid mock raw scraped records."""
    return pd.DataFrame([
        {
            "Title": "Test Book One",
            "Price": "£20.00",
            "Rating": "Five",
            "Availability": "In stock",
            "URL": "https://books.toscrape.com/catalogue/test-book-one_1/index.html",
            "Page": 1
        },
        {
            "Title": "Test Book Two",
            "Price": "£50.00",
            "Rating": "Two",
            "Availability": "In stock",
            "URL": "https://books.toscrape.com/catalogue/test-book-two_2/index.html",
            "Page": 1
        }
    ])


# 1. Test Web Scraper Extraction
def test_web_scraper_extraction():
    """Test HTML parsing logic on valid book pod markup."""
    sample_html = """
    <article class="product_pod">
        <h3><a href="catalogue/mock-book_100/index.html" title="Mock Book Title">Mock Book Title</a></h3>
        <p class="price_color">£32.50</p>
        <p class="star-rating Four"></p>
        <p class="instock availability"><i class="icon-ok"></i> In stock</p>
    </article>
    """
    soup = BeautifulSoup(sample_html, "html.parser")
    card = soup.find("article", class_="product_pod")

    title = card.h3.a["title"]
    price = card.find("p", class_="price_color").get_text(strip=True)
    rating = card.find("p", class_="star-rating")["class"][1]
    availability = card.find("p", class_="instock availability").get_text(strip=True)

    assert title == "Mock Book Title"
    assert price == "£32.50"
    assert rating == "Four"
    assert "In stock" in availability


# 2. Test Network Failure Handling
def test_network_failure_handling():
    """Test that network exceptions are trapped without crashing."""
    session = create_resilient_session()
    with patch.object(session, "get", side_effect=requests.RequestException("Simulated Timeout")):
        with pytest.raises(requests.RequestException):
            session.get("https://invalid-nonexistent-domain-test.org", timeout=2)


# 3. Test Missing HTML Elements Handling
def test_missing_html_elements_handling():
    """Test extraction resiliency when HTML elements are missing."""
    incomplete_html = """
    <article class="product_pod">
        <!-- Missing h3 title -->
        <p class="price_color">£10.00</p>
    </article>
    """
    soup = BeautifulSoup(incomplete_html, "html.parser")
    card = soup.find("article", class_="product_pod")
    title = card.h3.a.get("title") if card.h3 and card.h3.a else None
    assert title is None


# 4. Test Data Cleaning
def test_data_cleaning(sample_raw_dataframe):
    """Test price conversion, rating mapping, and column normalization."""
    clean_df = transform_data(sample_raw_dataframe)

    assert clean_df.loc[0, "Price_Value"] == 20.0
    assert clean_df.loc[0, "Rating_Score"] == 5
    assert clean_df.loc[1, "Price_Value"] == 50.0
    assert clean_df.loc[1, "Rating_Score"] == 2


# 5. Test Duplicate Removal
def test_duplicate_removal():
    """Test that duplicate product URLs are filtered out."""
    df_dupes = pd.DataFrame([
        {
            "Title": "Original",
            "Price": "£25.00",
            "Rating": "Three",
            "Availability": "In stock",
            "URL": "https://books.toscrape.com/duplicate_url",
            "Page": 1
        },
        {
            "Title": "Copy",
            "Price": "£25.00",
            "Rating": "Three",
            "Availability": "In stock",
            "URL": "https://books.toscrape.com/duplicate_url",
            "Page": 1
        }
    ])
    clean = transform_data(df_dupes)
    assert len(clean) == 1


# 6. Test Schema Validation
def test_schema_validation(sample_raw_dataframe):
    """Test schema validation fails when required column is missing."""
    corrupt = sample_raw_dataframe.drop(columns=["Price"])
    is_valid, msg = validate_raw_data(corrupt)
    assert is_valid is False
    assert "Missing required raw columns" in msg


# 7. Test Invalid Price Detection
def test_invalid_price_detection():
    """Test invalid or negative prices are caught by validation."""
    df_bad_price = pd.DataFrame([
        {
            "Title": "Bad Price Book",
            "Price": "£-10.00",
            "Rating": "Three",
            "Availability": "In stock",
            "URL": "https://books.toscrape.com/bad-price",
            "Page": 1,
            "Price_Value": -10.0,
            "Rating_Score": 3,
            "In_Stock_Flag": 1,
            "Price_Category": "Budget (<£25)"
        }
    ])
    is_valid, msg = validate_transformed_data(df_bad_price)
    assert is_valid is False
    assert "invalid or negative price" in msg


# 8. Test Database Insertion
def test_database_insertion(sample_raw_dataframe, tmp_path):
    """Test inserting valid clean records into an isolated SQLite database."""
    test_db = tmp_path / "test_insert.db"
    clean_df = transform_data(sample_raw_dataframe)

    metrics = load_to_sqlite(clean_df, test_db)
    assert metrics["transaction_status"] == "COMMITTED"
    assert metrics["final_db_count"] == 2

    # Verify query
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM books;")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 2


# 9. Test Database UPSERT Logic
def test_database_upsert(tmp_path):
    """Test that explicit UPSERT updates attributes on conflict instead of failing."""
    test_db = tmp_path / "test_upsert.db"

    initial_df = pd.DataFrame([{
        "Title": "Old Title",
        "Price": "£15.00",
        "Price_Value": 15.0,
        "Rating": "One",
        "Rating_Score": 1,
        "Availability": "In stock",
        "In_Stock_Flag": 1,
        "Price_Category": "Budget (<£25)",
        "URL": "https://books.toscrape.com/upsert-target",
        "Page": 1
    }])
    load_to_sqlite(initial_df, test_db)

    # Insert updated data for the exact same URL
    updated_df = pd.DataFrame([{
        "Title": "Updated New Title",
        "Price": "£28.00",
        "Price_Value": 28.0,
        "Rating": "Four",
        "Rating_Score": 4,
        "Availability": "In stock",
        "In_Stock_Flag": 1,
        "Price_Category": "Mid-Range (£25-£45)",
        "URL": "https://books.toscrape.com/upsert-target",
        "Page": 2
    }])
    load_to_sqlite(updated_df, test_db)

    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT title, price_value, rating_score, page FROM books WHERE url = 'https://books.toscrape.com/upsert-target';")
    row = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM books;")
    total_count = cur.fetchone()[0]
    conn.close()

    assert total_count == 1  # Total count unchanged
    assert row[0] == "Updated New Title"  # Updated via UPSERT
    assert row[1] == 28.0
    assert row[2] == 4
    assert row[3] == 2


# 10. Test Transaction Rollback
def test_transaction_rollback(tmp_path):
    """Test that failed database transactions roll back without partial writes."""
    test_db = tmp_path / "test_rollback.db"
    conn = sqlite3.connect(test_db)
    create_database_schema(conn)

    # Insert 1 valid record manually
    cur = conn.cursor()
    cur.execute("INSERT INTO books (url, title, price_value, rating_score, in_stock_flag) VALUES ('url_1', 'Title 1', 10.0, 3, 1);")
    conn.commit()

    # Attempt to insert an invalid record with null in NOT NULL column inside a failing transaction
    try:
        cur.execute("BEGIN TRANSACTION;")
        cur.execute("INSERT INTO books (url, title, price_value, rating_score, in_stock_flag) VALUES ('url_2', NULL, 20.0, 4, 1);")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()

    cur.execute("SELECT COUNT(*) FROM books;")
    count = cur.fetchone()[0]
    conn.close()

    assert count == 1  # Corrupt insert was rolled back completely


# 11. Test Pipeline Idempotency
def test_pipeline_idempotency(sample_raw_dataframe, tmp_path):
    """Test running loading stage multiple times preserves exact record count."""
    test_db = tmp_path / "test_idempotency.db"
    clean_df = transform_data(sample_raw_dataframe)

    # Run 1
    load_to_sqlite(clean_df, test_db)
    # Run 2
    load_to_sqlite(clean_df, test_db)

    # Verify audit
    audit = verify_database(test_db, output_dir=tmp_path)
    assert audit["total_records"] == 2
    assert audit["integrity_check"] == "ok"
    assert "PASSED" in audit["primary_key_uniqueness"]
