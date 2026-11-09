import logging
from pathlib import Path
import sqlite3
import pandas as pd

logger = logging.getLogger("DatheonETLPipeline")


def create_database_schema(conn: sqlite3.Connection) -> None:
    """
    Create the 'books' table with strict primary key constraint, data types,
    and performance indexes.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS books (
        url TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        price_raw TEXT,
        price_value REAL NOT NULL,
        rating_raw TEXT,
        rating_score INTEGER NOT NULL,
        availability TEXT,
        in_stock_flag INTEGER NOT NULL,
        price_category TEXT,
        page INTEGER,
        loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    create_price_index_sql = "CREATE INDEX IF NOT EXISTS idx_books_price ON books(price_value);"
    create_rating_index_sql = "CREATE INDEX IF NOT EXISTS idx_books_rating ON books(rating_score);"

    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    cursor.execute(create_price_index_sql)
    cursor.execute(create_rating_index_sql)
    conn.commit()
    logger.info("SQLite schema initialized: Table 'books' and indexes are ready.")


def load_to_sqlite(df: pd.DataFrame, db_path: Path) -> int:
    """
    Load clean records into SQLite database.
    Uses 'INSERT OR REPLACE' for idempotent upserting (prevents duplicate insertion).
    Employs strict transaction management (commit/rollback).
    """
    logger.info("==========================================")
    logger.info("STAGE 3: DATA LOADING (L)")
    logger.info("==========================================")

    if df is None or df.empty:
        raise ValueError("Cannot load empty DataFrame into SQLite.")

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Connecting to SQLite database: {db_path.name}")

    conn = sqlite3.connect(db_path)
    try:
        # Step 1: Ensure table schema exists
        create_database_schema(conn)

        # Step 2: Prepare record tuples for insertion
        records_to_insert = []
        for _, row in df.iterrows():
            records_to_insert.append((
                str(row["URL"]),
                str(row["Title"]),
                str(row.get("Price", "")),
                float(row["Price_Value"]),
                str(row.get("Rating", "")),
                int(row["Rating_Score"]),
                str(row.get("Availability", "")),
                int(row["In_Stock_Flag"]),
                str(row.get("Price_Category", "")),
                int(row.get("Page", 1))
            ))

        upsert_query = """
        INSERT OR REPLACE INTO books (
            url, title, price_raw, price_value, rating_raw,
            rating_score, availability, in_stock_flag, price_category, page
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        # Step 3: Execute in transaction
        cursor = conn.cursor()
        cursor.executemany(upsert_query, records_to_insert)
        conn.commit()
        logger.info(f"Database transaction committed: {len(records_to_insert)} records inserted/upserted.")

        # Step 4: Verification query
        cursor.execute("SELECT COUNT(*) FROM books;")
        total_in_db = cursor.fetchone()[0]

        cursor.execute("SELECT ROUND(AVG(price_value), 2), MIN(price_value), MAX(price_value) FROM books;")
        avg_p, min_p, max_p = cursor.fetchone()

        logger.info(f"Database Verification: Total records in 'books' table = {total_in_db}")
        logger.info(f"SQL Aggregate Check: Avg Price = £{avg_p}, Min = £{min_p}, Max = £{max_p}")

        return total_in_db

    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction FAILED! Rolled back changes. Error: {e}")
        raise e
    finally:
        conn.close()
        logger.info("SQLite database connection closed.")

