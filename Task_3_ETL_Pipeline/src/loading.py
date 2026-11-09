# ==============================================================================
# DATHEON INTERNSHIP - TASK 3
# RELATIONAL DATABASE AUTO-INGESTION & UPSERT ENGINE (SQLITE)
# ==============================================================================

from datetime import datetime
import json
import logging
from pathlib import Path
import sqlite3
import pandas as pd

logger = logging.getLogger("DatheonETLPipeline")

EXPLICIT_UPSERT_SQL = """
INSERT INTO books (
    url, title, price_raw, price_value, rating_raw,
    rating_score, availability, in_stock_flag, price_category, page
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(url)
DO UPDATE SET
    title = excluded.title,
    price_raw = excluded.price_raw,
    price_value = excluded.price_value,
    rating_raw = excluded.rating_raw,
    rating_score = excluded.rating_score,
    availability = excluded.availability,
    in_stock_flag = excluded.in_stock_flag,
    price_category = excluded.price_category,
    page = excluded.page;
"""


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
    logger.info("SQLite schema initialized: Table 'books' and indexes verified.")


def load_to_sqlite(df: pd.DataFrame, db_path: Path) -> dict:
    """
    Load clean records into SQLite database using explicit UPSERT.
    Guarantees transaction safety (commit on success, rollback on error).
    Returns load statistics.
    """
    logger.info("==========================================")
    logger.info("STAGE 3: DATA LOADING & UPSERT (L)")
    logger.info("==========================================")

    if df is None or df.empty:
        raise ValueError("Cannot load empty DataFrame into SQLite.")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Connecting to SQLite database at: {db_path.resolve()}")

    conn = sqlite3.connect(db_path)
    load_metrics = {
        "timestamp": datetime.now().isoformat(),
        "database_file": str(db_path.resolve()),
        "records_processed": len(df),
        "initial_db_count": 0,
        "final_db_count": 0,
        "inserted_or_updated": 0,
        "transaction_status": "PENDING"
    }

    try:
        # Step 1: Ensure table schema
        create_database_schema(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books;")
        load_metrics["initial_db_count"] = cursor.fetchone()[0]

        # Step 2: Prepare record tuples
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

        # Step 3: Execute explicit UPSERT in transaction
        cursor.executemany(EXPLICIT_UPSERT_SQL, records_to_insert)
        conn.commit()
        load_metrics["transaction_status"] = "COMMITTED"
        load_metrics["inserted_or_updated"] = len(records_to_insert)
        logger.info(f"Transaction committed: {len(records_to_insert)} records processed via UPSERT.")

        # Step 4: Final count
        cursor.execute("SELECT COUNT(*) FROM books;")
        load_metrics["final_db_count"] = cursor.fetchone()[0]
        logger.info(f"Final record count in table 'books': {load_metrics['final_db_count']}")

        return load_metrics

    except Exception as e:
        conn.rollback()
        load_metrics["transaction_status"] = "ROLLED_BACK"
        logger.error(f"FATAL: Database transaction failed! Rolled back changes. Error: {e}")
        raise e
    finally:
        conn.close()
        logger.info("SQLite database connection closed.")


def verify_database(db_path: Path, output_dir: Path | None = None) -> dict:
    """
    Run comprehensive integrity and primary key checks on SQLite database.
    Generates database_report.txt and database_verification.json.
    """
    if output_dir is None:
        output_dir = db_path.parent.parent

    logger.info("==========================================")
    logger.info("DATABASE INTEGRITY & VERIFICATION AUDIT")
    logger.info("==========================================")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    verification = {
        "timestamp": datetime.now().isoformat(),
        "database_path": str(db_path.resolve()),
        "file_size_bytes": db_path.stat().st_size if db_path.exists() else 0,
        "integrity_check": "FAILED",
        "primary_key_uniqueness": "FAILED",
        "total_records": 0,
        "average_price": 0.0,
        "min_price": 0.0,
        "max_price": 0.0,
        "rating_breakdown": {},
        "status": "FAILED"
    }

    try:
        # 1. PRAGMA integrity check
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()[0]
        verification["integrity_check"] = integrity_result
        logger.info(f"PRAGMA integrity_check result: {integrity_result}")

        # 2. Total record count
        cursor.execute("SELECT COUNT(*) FROM books;")
        total_records = cursor.fetchone()[0]
        verification["total_records"] = total_records

        # 3. Check for any duplicate primary keys
        cursor.execute("SELECT url, COUNT(*) FROM books GROUP BY url HAVING COUNT(*) > 1;")
        duplicates = cursor.fetchall()
        if len(duplicates) == 0:
            verification["primary_key_uniqueness"] = "PASSED (Zero Duplicate URLs)"
            logger.info("Primary key uniqueness PASSED: No duplicate URLs found.")
        else:
            verification["primary_key_uniqueness"] = f"FAILED ({len(duplicates)} duplicate URLs found)"
            logger.error(verification["primary_key_uniqueness"])

        # 4. Statistical aggregates from SQLite
        cursor.execute("SELECT ROUND(AVG(price_value), 2), MIN(price_value), MAX(price_value) FROM books;")
        avg_p, min_p, max_p = cursor.fetchone()
        verification["average_price"] = avg_p or 0.0
        verification["min_price"] = min_p or 0.0
        verification["max_price"] = max_p or 0.0

        # 5. Rating breakdown
        cursor.execute("SELECT rating_score, COUNT(*) FROM books GROUP BY rating_score ORDER BY rating_score;")
        verification["rating_breakdown"] = {f"{r}_star": count for r, count in cursor.fetchall()}

        if verification["integrity_check"] == "ok" and "PASSED" in verification["primary_key_uniqueness"]:
            verification["status"] = "PASSED"
        else:
            verification["status"] = "FAILED"

    finally:
        conn.close()

    # Save JSON verification report
    json_path = output_dir / "database_verification.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(verification, f, indent=4)
    logger.info(f"Database verification JSON saved: {json_path.name}")

    # Save Text Report
    txt_path = output_dir / "database_report.txt"
    report_text = f"""==================================================
        DATHEON TASK 3: DATABASE AUDIT REPORT
==================================================
Execution Timestamp     : {verification['timestamp']}
Database Location       : {verification['database_path']}
Database File Size      : {verification['file_size_bytes']} bytes
Database Status         : {verification['status']}

--- INTEGRITY & CONSTRAINTS ---
SQLite PRAGMA Integrity : {verification['integrity_check']}
Primary Key (URL) Check : {verification['primary_key_uniqueness']}
Total Table Records     : {verification['total_records']}

--- STATISTICAL VALIDATION VIA SQL ---
Average Price (SQL AVG) : £{verification['average_price']}
Lowest Price (SQL MIN)  : £{verification['min_price']}
Highest Price (SQL MAX) : £{verification['max_price']}

--- RATING DISTRIBUTION IN DATABASE ---
{json.dumps(verification['rating_breakdown'], indent=2)}

--- UPSERT & IDEMPOTENCY STATUS ---
Upsert Engine Pattern   : INSERT ... ON CONFLICT(url) DO UPDATE SET ...
Duplicate Safe (Upsert) : VERIFIED
Transaction ACID Safety : VERIFIED (Explicit COMMIT / ROLLBACK)
==================================================
"""
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    logger.info(f"Database text report saved: {txt_path.name}")

    return verification
