import logging
import pandas as pd

logger = logging.getLogger("DatheonETLPipeline")

RAW_REQUIRED_COLUMNS = ["Title", "Price", "Rating", "Availability", "URL", "Page"]
TRANSFORMED_REQUIRED_COLUMNS = [
    "Title", "Price", "Rating", "Availability", "URL", "Page",
    "Price_Value", "Rating_Score", "In_Stock_Flag", "Price_Category"
]


def validate_raw_data(df: pd.DataFrame) -> tuple[bool, str]:
    """
    Validate structure and completeness of extracted raw data.
    """
    if df is None or df.empty:
        msg = "Validation Error: Extracted DataFrame is empty or None."
        logger.error(msg)
        return False, msg

    missing_cols = [col for col in RAW_REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        msg = f"Validation Error: Missing required raw columns: {missing_cols}"
        logger.error(msg)
        return False, msg

    null_titles = df["Title"].isna().sum()
    null_urls = df["URL"].isna().sum()
    if null_titles > 0 or null_urls > 0:
        msg = f"Validation Warning: Found null Titles ({null_titles}) or null URLs ({null_urls})."
        logger.warning(msg)

    logger.info(f"Raw data validation PASSED: {len(df)} records with all required columns present.")
    return True, "Raw data valid."


def validate_transformed_data(df: pd.DataFrame) -> tuple[bool, str]:
    """
    Validate clean transformed data before database loading.
    """
    if df is None or df.empty:
        msg = "Validation Error: Transformed DataFrame is empty or None."
        logger.error(msg)
        return False, msg

    missing_cols = [col for col in TRANSFORMED_REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        msg = f"Validation Error: Missing required transformed columns: {missing_cols}"
        logger.error(msg)
        return False, msg

    # Validate price values (must be positive floats)
    invalid_prices = (df["Price_Value"] <= 0).sum() + df["Price_Value"].isna().sum()
    if invalid_prices > 0:
        msg = f"Validation Error: Found {invalid_prices} invalid or negative price values."
        logger.error(msg)
        return False, msg

    # Validate ratings (must be between 1 and 5)
    invalid_ratings = (~df["Rating_Score"].between(1, 5)).sum() + df["Rating_Score"].isna().sum()
    if invalid_ratings > 0:
        msg = f"Validation Error: Found {invalid_ratings} ratings outside 1-5 range."
        logger.error(msg)
        return False, msg

    # Validate duplicate URLs
    duplicate_urls = df.duplicated(subset=["URL"]).sum()
    if duplicate_urls > 0:
        msg = f"Validation Error: Found {duplicate_urls} duplicate URLs (Primary Key violation risk)."
        logger.error(msg)
        return False, msg

    logger.info(f"Transformed data validation PASSED: {len(df)} records are clean, typed, and valid.")
    return True, "Transformed data valid."

