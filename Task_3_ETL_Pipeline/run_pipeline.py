# ==============================================================================
# DATHEON INTERNSHIP - TASK 3
# AUTOMATED ETL PIPELINE ORCHESTRATOR
# ==============================================================================
# Run command: python run_pipeline.py [--scrape]
# ==============================================================================

import argparse
import sys
import time

from config import DB_PATH, FORCE_RE_SCRAPE, LOG_FILE_PATH, PROCESSED_CSV_PATH, PROCESSED_JSON_PATH
from src.extraction import extract_data
from src.loading import load_to_sqlite
from src.logger_config import setup_logger
from src.transformation import transform_data


def print_summary_report(
    extracted_count: int,
    transformed_count: int,
    loaded_count: int,
    duration: float,
    status: str
) -> None:
    """Print the final executive summary to console."""
    print("\n" + "=" * 50)
    print("             ETL PIPELINE SUMMARY")
    print("=" * 50)
    print(f"Extraction       : SUCCESS ({extracted_count} records)")
    print(f"Transformation   : SUCCESS ({transformed_count} records)")
    print(f"Loading (SQLite) : SUCCESS ({loaded_count} records)")
    print("-" * 50)
    print(f"Records Extracted : {extracted_count}")
    print(f"Records Processed : {transformed_count}")
    print(f"Records Loaded    : {loaded_count}")
    print("-" * 50)
    print(f"CSV Export       : SUCCESS ({PROCESSED_CSV_PATH.name})")
    print(f"JSON Export      : SUCCESS ({PROCESSED_JSON_PATH.name})")
    print(f"Database Storage : SUCCESS ({DB_PATH.name} -> table 'books')")
    print("-" * 50)
    print(f"Pipeline Status  : {status}")
    print(f"Total Duration   : {duration:.2f} seconds")
    print("=" * 50 + "\n")


def run_pipeline(force_scrape: bool = False) -> bool:
    """
    Execute the automated ETL pipeline end-to-end:
    Extract -> Transform -> Load
    """
    logger = setup_logger(LOG_FILE_PATH)
    logger.info("**************************************************")
    logger.info("DATHEON AUTOMATED ETL PIPELINE EXECUTION STARTED")
    logger.info(f"Configuration: FORCE_RE_SCRAPE = {force_scrape}")
    logger.info("**************************************************")

    start_time = time.time()
    extracted_count = 0
    transformed_count = 0
    loaded_count = 0

    try:
        # Step 1: Extraction
        raw_df = extract_data(force_scrape=force_scrape)
        extracted_count = len(raw_df)

        # Step 2: Transformation
        clean_df = transform_data(raw_df)
        transformed_count = len(clean_df)

        # Step 3: Loading
        loaded_count = load_to_sqlite(clean_df, DB_PATH)

        duration = time.time() - start_time
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")

        print_summary_report(
            extracted_count=extracted_count,
            transformed_count=transformed_count,
            loaded_count=loaded_count,
            duration=duration,
            status="COMPLETED"
        )
        return True

    except Exception as e:
        duration = time.time() - start_time
        logger.critical(f"FATAL: Pipeline execution halted due to unhandled error: {e}", exc_info=True)
        print_summary_report(
            extracted_count=extracted_count,
            transformed_count=transformed_count,
            loaded_count=loaded_count,
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

