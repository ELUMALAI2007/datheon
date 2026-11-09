from pathlib import Path

# ==============================================================================
# PIPELINE DIRECTORY CONFIGURATION
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

DATABASE_DIR = BASE_DIR / "database"
LOGS_DIR = BASE_DIR / "logs"
TESTS_DIR = BASE_DIR / "tests"

# Ensure runtime directories exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, DATABASE_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# FILE PATHS
# ==============================================================================
RAW_CSV_PATH = RAW_DATA_DIR / "books_raw.csv"
RAW_JSON_PATH = RAW_DATA_DIR / "books_raw.json"

PROCESSED_CSV_PATH = PROCESSED_DATA_DIR / "books_transformed.csv"
PROCESSED_JSON_PATH = PROCESSED_DATA_DIR / "books_transformed.json"

DB_PATH = DATABASE_DIR / "books.db"
LOG_FILE_PATH = LOGS_DIR / "pipeline.log"

# ==============================================================================
# SCRAPER & EXTRACTION SETTINGS
# ==============================================================================
SCRAPER_URL = "https://books.toscrape.com/"
MAX_RECORDS_TARGET = 100
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DatheonETLPipeline/1.0"

# Setting to avoid re-scraping if raw data exists and is valid
FORCE_RE_SCRAPE = False

