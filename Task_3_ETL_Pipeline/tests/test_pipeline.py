from pathlib import Path
import sqlite3
import sys

# Ensure Task_3_ETL_Pipeline root is on sys.path
TEST_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TEST_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import pandas as pd
import pytest

from src.loading import create_database_schema, load_to_sqlite
from src.transformation import transform_data
from src.validation import validate_raw_data, validate_transformed_data


@pytest.fixture
def sample_raw_dataframe():
    """Fixture providing mock raw scraped records."""
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


def test_raw_data_validation(sample_raw_dataframe):
    """Test validation detects valid and corrupt raw data."""
    is_valid, msg = validate_raw_data(sample_raw_dataframe)
    assert is_valid is True

    # Test missing column
    corrupt_df = sample_raw_dataframe.drop(columns=["Price"])
    is_valid_bad, msg_bad = validate_raw_data(corrupt_df)
    assert is_valid_bad is False
    assert "Missing required raw columns" in msg_bad


def test_transformation_logic(sample_raw_dataframe):
    """Test data cleaning, price conversion, and calculated fields."""
    clean_df = transform_data(sample_raw_dataframe)

    assert len(clean_df) == 2
    assert "Price_Value" in clean_df.columns
    assert "Rating_Score" in clean_df.columns
    assert "Price_Category" in clean_df.columns
    assert "In_Stock_Flag" in clean_df.columns

    # Verify conversions
    assert clean_df.loc[0, "Price_Value"] == 20.0
    assert clean_df.loc[0, "Rating_Score"] == 5
    assert clean_df.loc[0, "Price_Category"] == "Budget (<£25)"
    assert clean_df.loc[0, "In_Stock_Flag"] == 1

    assert clean_df.loc[1, "Price_Value"] == 50.0
    assert clean_df.loc[1, "Rating_Score"] == 2
    assert clean_df.loc[1, "Price_Category"] == "Premium (>£45)"


def test_duplicate_url_deduplication():
    """Test that duplicate URLs are dropped during transformation."""
    df_with_dupes = pd.DataFrame([
        {
            "Title": "Duplicate Book",
            "Price": "£15.00",
            "Rating": "Three",
            "Availability": "In stock",
            "URL": "https://books.toscrape.com/catalogue/same-url/index.html",
            "Page": 1
        },
        {
            "Title": "Duplicate Book Copy",
            "Price": "£15.00",
            "Rating": "Three",
            "Availability": "In stock",
            "URL": "https://books.toscrape.com/catalogue/same-url/index.html",
            "Page": 1
        }
    ])
    clean_df = transform_data(df_with_dupes)
    assert len(clean_df) == 1


def test_sqlite_loading_and_idempotency(sample_raw_dataframe, tmp_path):
    """Test loading into an isolated temporary SQLite database."""
    test_db = tmp_path / "test_books.db"
    clean_df = transform_data(sample_raw_dataframe)

    # First load
    count_1 = load_to_sqlite(clean_df, test_db)
    assert count_1 == 2

    # Second load with identical records (idempotency check: count should remain 2, not 4)
    count_2 = load_to_sqlite(clean_df, test_db)
    assert count_2 == 2

    # Verify directly via SQL query
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT title, price_value, rating_score FROM books WHERE price_value = 20.0;")
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "Test Book One"
    assert row[1] == 20.0
    assert row[2] == 5
