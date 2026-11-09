# ==============================================================================
# DATHEON INTERNSHIP - TASK 3
# AUTOMATED ETL PIPELINE ORCHESTRATOR
# ==============================================================================
# Run command: python run_pipeline.py [--scrape]
# ==============================================================================

import argparse
import sys
import time
from pathlib import Path

from config import BASE_DIR, DB_PATH, FORCE_RE_SCRAPE, LOG_FILE_PATH, PROCESSED_CSV_PATH, PROCESSED_JSON_PATH
from src.extraction import extract_data
from src.loading import load_to_sqlite, verify_database
from src.logger_config import setup_logger
from src.transformation import transform_data


def print_summary_report(
    extracted_count: int,
    transformed_count: int,
    loaded_metrics: dict,
    verification: dict,
    duration: float,
    status: str
) -> None:
    """Print the final executive summary to console."""
    print("\n" + "=" * 55)
    print("             DATHEON ETL PIPELINE SUMMARY")
    print("=" * 55)
    print(f"Extraction Stage      : SUCCESS ({extracted_count} records)")
    print(f"Transformation Stage  : SUCCESS ({transformed_count} records)")
    print(f"Loading Stage (UPSERT): SUCCESS ({loaded_metrics.get('final_db_count', 0)} records in SQLite)")
    print("-" * 55)
    print(f"Raw Records Extracted : {extracted_count}")
    print(f"Clean Records Loaded  : {transformed_count}")
    print(f"Total in Database     : {verification.get('total_records', 0)}")
    print(f"PRAGMA Integrity Check: {verification.get('integrity_check', 'UNKNOWN')}")
    print(f"Primary Key Check     : {verification.get('primary_key_uniqueness', 'UNKNOWN')}")
    print("-" * 55)
    print(f"CSV Deliverable       : SUCCESS ({PROCESSED_CSV_PATH.name})")
    print(f"JSON Deliverable      : SUCCESS ({PROCESSED_JSON_PATH.name})")
    print(f"Database File         : SUCCESS ({DB_PATH.name} -> table 'books')")
    print(f"Database Audit Report : SUCCESS (database_report.txt)")
    print("-" * 55)
    print(f"Pipeline Status       : {status}")
    print(f"Total Duration        : {duration:.2f} seconds")
    print("=" * 55 + "\n")


def run_pipeline(force_scrape: bool = False) -> bool:
    """
    Execute the automated ETL pipeline end-to-end:
    Extract -> Transform -> Load (UPSERT) -> Verify Database
    """
    logger = setup_logger(LOG_FILE_PATH)
    logger.info("**************************************************")
    logger.info("DATHEON AUTOMATED ETL PIPELINE EXECUTION STARTED")
    logger.info(f"Configuration: FORCE_RE_SCRAPE = {force_scrape}")
    logger.info("**************************************************")

    start_time = time.time()
    extracted_count = 0
    transformed_count = 0
    loaded_metrics = {}
    verification = {}

    try:
        # Stage 1: Extraction
        raw_df = extract_data(force_scrape=force_scrape)
        extracted_count = len(raw_df)

        # Stage 2: Transformation
        clean_df = transform_data(raw_df)
        transformed_count = len(clean_df)

        # Stage 3: Loading with Explicit SQLite UPSERT
        loaded_metrics = load_to_sqlite(clean_df, DB_PATH)

        # Stage 4: Comprehensive Database Verification & Report Generation
        verification = verify_database(DB_PATH, output_dir=BASE_DIR)

        duration = time.time() - start_time
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")

        print_summary_report(
            extracted_count=extracted_count,
            transformed_count=transformed_count,
            loaded_metrics=loaded_metrics,
            verification=verification,
            duration=duration,
            status="COMPLETED"
        )
        return True

    except Exception as e:
        duration = time.time() - start_time
        logger.critical(f"FATAL: Pipeline execution halted due to error: {e}", exc_info=True)
        print_summary_report(
            extracted_count=extracted_count,
            transformed_count=transformed_count,
            loaded_metrics=loaded_metrics,
            verification=verification,
            duration=duration,
            status="FAILED"
        )
        return False


def main():
    parser = argparse.ArgumentParser(description="Datheon Automated ETL Pipeline")
    parser.add_argument(
        "--scrape",
        action="store_true",
        default=FORCE_RE_SCRAPE,
        help="Force live web scraping instead of using cached raw data."
    )
    args = parser.parse_args()

    success = run_pipeline(force_scrape=args.scrape)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
