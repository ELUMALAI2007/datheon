import logging
import numpy as np
import pandas as pd

from config import PROCESSED_CSV_PATH, PROCESSED_JSON_PATH
from src.validation import validate_transformed_data

logger = logging.getLogger("DatheonETLPipeline")

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main transformation entry point.
    Cleans strings, converts numeric types, adds calculated columns,
    and deduplicates records based on unique product URLs.
    """
    logger.info("==========================================")
    logger.info("STAGE 2: DATA TRANSFORMATION (T)")
    logger.info("==========================================")

    if df is None or df.empty:
        raise ValueError("Cannot transform empty or None DataFrame.")

    df = df.copy()
    initial_count = len(df)

    # 1. Standardize string fields and trim whitespaces
    df["Title"] = df["Title"].astype(str).str.strip()
    df["URL"] = df["URL"].astype(str).str.strip()
    df["Availability"] = df["Availability"].astype(str).str.strip()

    # 2. Deduplicate records based on unique product URL
    df = df.drop_duplicates(subset=["URL"]).reset_index(drop=True)
    duplicates_removed = initial_count - len(df)
    if duplicates_removed > 0:
        logger.warning(f"Deduplication: Dropped {duplicates_removed} duplicate records by URL.")
    else:
        logger.info("Deduplication: Zero duplicate URLs detected.")

    # 3. Numeric conversion of Price (strip '£' symbol)
    if "Price_Value" not in df.columns or df["Price_Value"].isna().any():
        df["Price_Value"] = pd.to_numeric(
            df["Price"].astype(str).str.replace("£", "", regex=False).str.strip(),
            errors="coerce"
        )
    else:
        df["Price_Value"] = df["Price_Value"].astype(float)

    # 4. Map text ratings into numeric integer scores (1-5)
    if "Rating_Score" not in df.columns or df["Rating_Score"].isna().any():
        df["Rating_Score"] = df["Rating"].map(RATING_MAP)
    else:
        df["Rating_Score"] = df["Rating_Score"].astype(int)

    # 5. Feature Engineering: In_Stock_Flag (Integer 1 / 0 for SQLite compatibility)
    df["In_Stock_Flag"] = df["Availability"].str.lower().str.contains("in stock").astype(int)

    # 6. Feature Engineering: Price_Category ('Budget', 'Mid-Range', 'Premium')
    bins = [0, 25.0, 45.0, np.inf]
    labels = ["Budget (<£25)", "Mid-Range (£25-£45)", "Premium (>£45)"]
    df["Price_Category"] = pd.cut(df["Price_Value"], bins=bins, labels=labels, right=True).astype(str)

    # 7. Drop records with missing values in vital columns
    clean_df = df.dropna(subset=["Title", "URL", "Price_Value", "Rating_Score"]).reset_index(drop=True)
    dropped_nulls = len(df) - len(clean_df)
    if dropped_nulls > 0:
        logger.warning(f"Data Cleaning: Dropped {dropped_nulls} records with missing vital fields.")

    # 8. Validate transformed dataset
    is_valid, msg = validate_transformed_data(clean_df)
    if not is_valid:
        raise ValueError(f"Transformation stage failed validation: {msg}")

    # 9. Persist processed deliverables (Silver Layer)
    clean_df.to_csv(PROCESSED_CSV_PATH, index=False, encoding="utf-8-sig")
    clean_df.to_json(PROCESSED_JSON_PATH, orient="records", indent=4, force_ascii=False)
    logger.info(f"Transformed data exported to {PROCESSED_CSV_PATH.name} and {PROCESSED_JSON_PATH.name}")
    logger.info(f"Transformation completed: {len(clean_df)} clean records prepared.")

    return clean_df

