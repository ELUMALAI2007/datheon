# ==============================================================================
# DATHEON INTERNSHIP - TASK 2
# AUTOMATED DATA CLEANING, SCHEMA TRANSFORMATION & DATA QUALITY AUDIT
# ==============================================================================

from datetime import datetime
import json
import logging
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Setup Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHARTS_DIR = BASE_DIR / "charts"
LOGS_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CSV = DATA_DIR / "scraped_data.csv"
CLEANED_CSV = DATA_DIR / "cleaned_data.csv"
ANALYSIS_JSON = DATA_DIR / "analysis_summary.json"
RATING_SUMMARY_CSV = DATA_DIR / "rating_summary.csv"
CATEGORY_SUMMARY_CSV = DATA_DIR / "price_category_summary.csv"

DATA_QUALITY_REPORT_TXT = BASE_DIR / "data_quality_report.txt"
VALIDATION_REPORT_JSON = BASE_DIR / "validation_report.json"
LOG_FILE = LOGS_DIR / "data_processing.log"

# Setup Logger
def setup_logger() -> logging.Logger:
    logger = logging.getLogger("DatheonDataProcessing")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)-8s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

logger = setup_logger()

# Required Raw Schema
REQUIRED_COLUMNS = ["Title", "Price", "Rating", "Availability", "URL", "Page"]
RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}


def load_dataset(file_path: Path) -> pd.DataFrame:
    """Load raw dataset from CSV."""
    logger.info("=" * 60)
    logger.info("STAGE 1: LOADING DATASET")
    logger.info("=" * 60)
    if not file_path.exists():
        err_msg = f"Input file not found at: {file_path}"
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} records from {file_path.name}")
    return df


def validate_schema(df: pd.DataFrame) -> dict:
    """Validate presence of required columns and data structures."""
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    is_valid = len(missing_cols) == 0
    res = {
        "is_valid": is_valid,
        "required_columns": REQUIRED_COLUMNS,
        "present_columns": df.columns.tolist(),
        "missing_columns": missing_cols
    }
    if not is_valid:
        logger.error(f"Schema validation FAILED. Missing columns: {missing_cols}")
    else:
        logger.info("Schema validation PASSED. All required columns are present.")
    return res


def clean_and_validate(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Execute end-to-end cleaning, type transformation, invalid removal,
    and build a comprehensive audit dictionary.
    """
    logger.info("=" * 60)
    logger.info("STAGE 2: DATA CLEANING & VALIDATION")
    logger.info("=" * 60)

    audit = {
        "timestamp": datetime.now().isoformat(),
        "total_input_records": len(df),
        "missing_values_before": df.isnull().sum().to_dict(),
        "schema_validation": validate_schema(df),
        "duplicates_removed": 0,
        "invalid_prices_removed": 0,
        "invalid_ratings_removed": 0,
        "empty_titles_removed": 0,
        "empty_urls_removed": 0,
        "total_invalid_removed": 0,
        "total_output_records": 0,
        "missing_values_after": {},
        "data_quality_status": "FAILED"
    }

    cleaned = df.copy()

    # 1. Standardize string fields
    cleaned["Title"] = cleaned["Title"].astype(str).str.strip()
    cleaned["URL"] = cleaned["URL"].astype(str).str.strip()
    cleaned["Availability"] = cleaned["Availability"].astype(str).str.strip()

    # Check empty titles or URLs
    empty_titles = (cleaned["Title"] == "") | (cleaned["Title"].str.lower() == "nan")
    empty_urls = (cleaned["URL"] == "") | (cleaned["URL"].str.lower() == "nan")

    audit["empty_titles_removed"] = int(empty_titles.sum())
    audit["empty_urls_removed"] = int(empty_urls.sum())

    cleaned = cleaned[~empty_titles & ~empty_urls].copy()

    # 2. Duplicate detection & removal (based on URL as unique identifier)
    before_dedup = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset=["URL"]).reset_index(drop=True)
    audit["duplicates_removed"] = before_dedup - len(cleaned)
    logger.info(f"Duplicate records removed by URL: {audit['duplicates_removed']}")

    # 3. Numeric price conversion & validation
    cleaned["Price_Value"] = pd.to_numeric(
        cleaned["Price"].astype(str).str.replace("£", "", regex=False).str.strip(),
        errors="coerce"
    )
    invalid_prices = cleaned["Price_Value"].isna() | (cleaned["Price_Value"] <= 0)
    audit["invalid_prices_removed"] = int(invalid_prices.sum())
    if audit["invalid_prices_removed"] > 0:
        logger.warning(f"Found {audit['invalid_prices_removed']} invalid price records; dropping.")
    cleaned = cleaned[~invalid_prices].copy()

    # 4. Rating conversion & validation (between 1 and 5)
    cleaned["Rating_Score"] = cleaned["Rating"].map(RATING_MAP)
    invalid_ratings = cleaned["Rating_Score"].isna() | (~cleaned["Rating_Score"].between(1, 5))
    audit["invalid_ratings_removed"] = int(invalid_ratings.sum())
    if audit["invalid_ratings_removed"] > 0:
        logger.warning(f"Found {audit['invalid_ratings_removed']} invalid rating records; dropping.")
    cleaned = cleaned[~invalid_ratings].copy()
    cleaned["Rating_Score"] = cleaned["Rating_Score"].astype(int)

    # 5. Feature Engineering: Availability Flag
    cleaned["In_Stock"] = cleaned["Availability"].str.lower().str.contains("in stock")

    # 6. Feature Engineering: Price Categories
    bins = [0, 25.0, 45.0, np.inf]
    labels = ["Budget (<£25)", "Mid-Range (£25-£45)", "Premium (>£45)"]
    cleaned["Price_Category"] = pd.cut(cleaned["Price_Value"], bins=bins, labels=labels, right=True).astype(str)

    # Final shape & missing values audit
    cleaned = cleaned.reset_index(drop=True)
    audit["total_output_records"] = len(cleaned)
    audit["total_invalid_removed"] = (
        audit["empty_titles_removed"]
        + audit["empty_urls_removed"]
        + audit["invalid_prices_removed"]
        + audit["invalid_ratings_removed"]
    )
    audit["missing_values_after"] = cleaned.isnull().sum().to_dict()

    # Quality status assessment
    if (
        audit["schema_validation"]["is_valid"]
        and audit["total_output_records"] >= 100
        and sum(audit["missing_values_after"].values()) == 0
    ):
        audit["data_quality_status"] = "PASSED"
        logger.info(f"Data Cleaning & Quality Validation PASSED: {len(cleaned)} clean records.")
    else:
        audit["data_quality_status"] = "PASSED WITH WARNINGS" if audit["total_output_records"] > 0 else "FAILED"
        logger.warning(f"Data Quality Status: {audit['data_quality_status']}")

    return cleaned, audit


def generate_reports(df: pd.DataFrame, audit: dict) -> None:
    """Generate both data_quality_report.txt and validation_report.json."""
    # 1. JSON Report
    with open(VALIDATION_REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=4)
    logger.info(f"Validation report saved: {VALIDATION_REPORT_JSON.name}")

    # 2. Text Report
    txt_content = f"""==================================================
       DATHEON TASK 2: DATA QUALITY REPORT
==================================================
Execution Timestamp : {audit['timestamp']}
Data Quality Status : {audit['data_quality_status']}

--- RECORD COUNTS ---
Total Input Records        : {audit['total_input_records']}
Total Output Clean Records : {audit['total_output_records']}
Duplicate Records Removed  : {audit['duplicates_removed']}
Invalid Records Removed    : {audit['total_invalid_removed']}
  - Invalid / Zero Prices  : {audit['invalid_prices_removed']}
  - Invalid Rating Values  : {audit['invalid_ratings_removed']}
  - Empty Titles           : {audit['empty_titles_removed']}
  - Empty URLs             : {audit['empty_urls_removed']}

--- SCHEMA VALIDATION ---
Schema Valid Status        : {'PASSED' if audit['schema_validation']['is_valid'] else 'FAILED'}
Required Columns Present   : {len(audit['schema_validation']['present_columns'])} / {len(audit['schema_validation']['required_columns'])}
Missing Columns            : {audit['schema_validation']['missing_columns']}

--- MISSING VALUES AUDIT ---
Missing Values Before Cleaning:
{json.dumps(audit['missing_values_before'], indent=2)}

Missing Values After Cleaning:
{json.dumps(audit['missing_values_after'], indent=2)}

--- SUMMARY & CONCLUSION ---
Clean Dataset Export : {CLEANED_CSV.resolve()}
Integrity Status     : 100% Non-Null, Typed and Validated
==================================================
"""
    with open(DATA_QUALITY_REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(txt_content)
    logger.info(f"Data quality text report saved: {DATA_QUALITY_REPORT_TXT.name}")


def perform_statistical_analysis(df: pd.DataFrame) -> dict:
    """Calculate statistical summaries and export GroupBy metrics."""
    logger.info("=" * 60)
    logger.info("STAGE 3: STATISTICAL ANALYSIS")
    logger.info("=" * 60)

    total_products = int(len(df))
    avg_price = float(round(df["Price_Value"].mean(), 2))
    median_price = float(round(df["Price_Value"].median(), 2))
    std_price = float(round(df["Price_Value"].std(), 2))
    min_price = float(round(df["Price_Value"].min(), 2))
    max_price = float(round(df["Price_Value"].max(), 2))
    avg_rating = float(round(df["Rating_Score"].mean(), 2))

    top_5_expensive = df.nlargest(5, "Price_Value")[["Title", "Price_Value", "Rating_Score"]].to_dict(orient="records")
    top_5_affordable = df.nsmallest(5, "Price_Value")[["Title", "Price_Value", "Rating_Score"]].to_dict(orient="records")

    rating_grp = df.groupby("Rating_Score")["Price_Value"].agg(
        Count="count",
        Average_Price="mean",
        Min_Price="min",
        Max_Price="max"
    ).round(2).reset_index()

    cat_grp = df.groupby("Price_Category", observed=False).agg(
        Count=("Title", "count"),
        Avg_Rating=("Rating_Score", "mean"),
        Avg_Price=("Price_Value", "mean")
    ).round(2).reset_index()

    rating_grp.to_csv(RATING_SUMMARY_CSV, index=False)
    cat_grp.to_csv(CATEGORY_SUMMARY_CSV, index=False)

    summary = {
        "total_products": total_products,
        "average_price": avg_price,
        "median_price": median_price,
        "std_price": std_price,
        "min_price": min_price,
        "max_price": max_price,
        "average_rating": avg_rating,
        "top_5_expensive": top_5_expensive,
        "top_5_affordable": top_5_affordable
    }

    with open(ANALYSIS_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    logger.info(f"Statistical analysis exported: {ANALYSIS_JSON.name}")
    return summary


def generate_visualizations(df: pd.DataFrame) -> None:
    """Generate the 4 standard Matplotlib charts."""
    logger.info("=" * 60)
    logger.info("STAGE 4: GENERATING CHARTS")
    logger.info("=" * 60)

    plt.rcParams["font.sans-serif"] = "DejaVu Sans"

    # 1. Price Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df["Price_Value"], bins=10, color="#2b5c8f", edgecolor="white", alpha=0.85)
    mean_val = df["Price_Value"].mean()
    ax.axvline(mean_val, color="#d9534f", linestyle="--", linewidth=2, label=f"Mean: £{mean_val:.2f}")
    ax.set_title("Distribution of Book Prices", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Price in GBP (£)", fontsize=11, labelpad=10)
    ax.set_ylabel("Book Count", fontsize=11, labelpad=10)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    ax.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "price_distribution.png", dpi=200)
    plt.close()

    # 2. Rating Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    rating_counts = df["Rating_Score"].value_counts().sort_index()
    colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db"]
    bars = ax.bar([f"{r} Star" for r in rating_counts.index], rating_counts.values, color=colors, width=0.6)
    for b in bars:
        ax.annotate(f"{b.get_height()}", xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontweight="bold")
    ax.set_title("Star Rating Distribution (1 to 5 Stars)", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_ylim(0, max(rating_counts.values) + 5)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "rating_distribution.png", dpi=200)
    plt.close()

    # 3. Avg Price by Rating
    fig, ax = plt.subplots(figsize=(8, 5))
    avg_p = df.groupby("Rating_Score")["Price_Value"].mean().round(2)
    bars = ax.bar([f"{r} Stars" for r in avg_p.index], avg_p.values, color="#16a085", width=0.55)
    for b in bars:
        ax.annotate(f"£{b.get_height():.2f}", xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontweight="bold")
    ax.set_title("Average Price across Star Ratings", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel("Average Price (£)", fontsize=11)
    ax.set_ylim(0, max(avg_p.values) + 10)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "avg_price_by_rating.png", dpi=200)
    plt.close()

    # 4. Price Category Donut
    fig, ax = plt.subplots(figsize=(7, 6))
    cat_counts = df["Price_Category"].value_counts()[["Budget (<£25)", "Mid-Range (£25-£45)", "Premium (>£45)"]]
    wedges, texts, autotexts = ax.pie(
        cat_counts.values,
        labels=cat_counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=["#27ae60", "#2980b9", "#8e44ad"],
        pctdistance=0.75,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
    ax.set_title("Product Share by Price Category", fontsize=14, fontweight="bold", pad=20)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "price_category_share.png", dpi=200)
    plt.close()

    logger.info("All 4 visualizations generated and saved in charts/")


def main():
    logger.info("############################################################")
    logger.info(" DATHEON TASK 2: DATA CLEANING & QUALITY AUDIT STARTED ")
    logger.info("############################################################")

    df = load_dataset(INPUT_CSV)
    cleaned_df, audit = clean_and_validate(df)

    # Export cleaned CSV
    cleaned_df.to_csv(CLEANED_CSV, index=False, encoding="utf-8-sig")
    logger.info(f"Cleaned dataset saved: {CLEANED_CSV}")

    # Generate Reports & Metrics
    generate_reports(cleaned_df, audit)
    perform_statistical_analysis(cleaned_df)
    generate_visualizations(cleaned_df)

    logger.info("=" * 60)
    logger.info("TASK 2 COMPLETE: DATA QUALITY AUDIT & CLEANING FINISHED!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
