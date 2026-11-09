# ==============================================================================
# DATHEON INTERNSHIP - TASK 2
# DATA PROCESSING, EXPLORATORY DATA ANALYSIS & VISUALIZATION
# ==============================================================================

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Setup Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHARTS_DIR = BASE_DIR / "charts"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CSV = DATA_DIR / "scraped_data.csv"
CLEANED_CSV = DATA_DIR / "cleaned_data.csv"
ANALYSIS_JSON = DATA_DIR / "analysis_summary.json"
RATING_SUMMARY_CSV = DATA_DIR / "rating_summary.csv"
CATEGORY_SUMMARY_CSV = DATA_DIR / "price_category_summary.csv"


def load_data(file_path: Path) -> pd.DataFrame:
    """Load raw dataset from CSV."""
    print("=" * 60)
    print("1. LOADING DATASET")
    print("=" * 60)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found at: {file_path}")
    df = pd.read_csv(file_path)
    print(f"Loaded {len(df)} records from {file_path.name}")
    return df


def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform thorough data cleaning, type conversions, and feature engineering.
    """
    print("\n" + "=" * 60)
    print("2. DATA CLEANING & FEATURE ENGINEERING")
    print("=" * 60)

    # 1. Clean Title and remove whitespace
    df["Title"] = df["Title"].astype(str).str.strip()

    # 2. Drop duplicates based on Title and URL
    initial_len = len(df)
    df = df.drop_duplicates(subset=["Title", "URL"]).copy()
    duplicates_removed = initial_len - len(df)
    print(f"Duplicate records removed: {duplicates_removed}")

    # 3. Clean and convert Price to float
    if "Price_Value" not in df.columns or df["Price_Value"].isna().any():
        df["Price_Value"] = pd.to_numeric(
            df["Price"].astype(str).str.replace("£", "", regex=False).str.strip(),
            errors="coerce"
        )

    # 4. Map star ratings to numeric scores (1 to 5)
    rating_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    if "Rating_Score" not in df.columns or df["Rating_Score"].isna().any():
        df["Rating_Score"] = df["Rating"].map(rating_map)

    # 5. Availability feature engineering (Boolean flag)
    df["In_Stock"] = df["Availability"].astype(str).str.lower().str.contains("in stock")

    # 6. Feature Engineering: Price Categories
    # Budget (< £25), Mid-Range (£25 - £45), Premium (> £45)
    bins = [0, 25.0, 45.0, np.inf]
    labels = ["Budget (<£25)", "Mid-Range (£25-£45)", "Premium (>£45)"]
    df["Price_Category"] = pd.cut(df["Price_Value"], bins=bins, labels=labels, right=True)

    # 7. Drop rows with nulls in vital fields
    df = df.dropna(subset=["Title", "Price_Value", "Rating_Score"]).reset_index(drop=True)
    print(f"Total clean records ready for analysis: {len(df)}")
    return df


def perform_statistical_analysis(df: pd.DataFrame) -> dict:
    """
    Calculate statistical summaries, aggregations, and business metrics.
    """
    print("\n" + "=" * 60)
    print("3. STATISTICAL ANALYSIS & AGGREGATIONS")
    print("=" * 60)

    # Core price metrics
    total_products = int(len(df))
    avg_price = float(round(df["Price_Value"].mean(), 2))
    median_price = float(round(df["Price_Value"].median(), 2))
    std_price = float(round(df["Price_Value"].std(), 2))
    min_price = float(round(df["Price_Value"].min(), 2))
    max_price = float(round(df["Price_Value"].max(), 2))

    # Rating distribution
    rating_counts = df["Rating_Score"].value_counts().sort_index().to_dict()
    avg_rating = float(round(df["Rating_Score"].mean(), 2))

    # Stock availability
    in_stock_count = int(df["In_Stock"].sum())

    # Top 5 Most Expensive Books
    top_5_expensive = df.nlargest(5, "Price_Value")[["Title", "Price_Value", "Rating_Score"]].to_dict(orient="records")

    # Top 5 Most Affordable Books
    top_5_affordable = df.nsmallest(5, "Price_Value")[["Title", "Price_Value", "Rating_Score"]].to_dict(orient="records")

    # GroupBy Rating Analysis
    rating_grp = df.groupby("Rating_Score")["Price_Value"].agg(
        Count="count",
        Average_Price="mean",
        Min_Price="min",
        Max_Price="max"
    ).round(2).reset_index()

    # GroupBy Price Category Analysis
    cat_grp = df.groupby("Price_Category", observed=False).agg(
        Count=("Title", "count"),
        Avg_Rating=("Rating_Score", "mean"),
        Avg_Price=("Price_Value", "mean")
    ).round(2).reset_index()

    print("\n--- Overall Summary Metrics ---")
    print(f"Total Products Scraped : {total_products}")
    print(f"Average Price (Mean)   : £{avg_price}")
    print(f"Median Price           : £{median_price}")
    print(f"Standard Deviation     : £{std_price}")
    print(f"Price Range            : £{min_price} - £{max_price}")
    print(f"Average Rating Score   : {avg_rating} / 5.0")
    print(f"In Stock Items         : {in_stock_count} / {total_products}")

    print("\n--- GroupBy Rating Summary ---")
    print(rating_grp.to_string(index=False))

    print("\n--- GroupBy Price Category Summary ---")
    print(cat_grp.to_string(index=False))

    print("\n--- Top 3 Most Expensive Books ---")
    for i, b in enumerate(top_5_expensive[:3], 1):
        print(f"{i}. {b['Title']} - £{b['Price_Value']} ({b['Rating_Score']} Stars)")

    # Save summary tables to CSV
    rating_grp.to_csv(RATING_SUMMARY_CSV, index=False)
    cat_grp.to_csv(CATEGORY_SUMMARY_CSV, index=False)

    summary_results = {
        "total_products": total_products,
        "average_price": avg_price,
        "median_price": median_price,
        "std_price": std_price,
        "min_price": min_price,
        "max_price": max_price,
        "average_rating": avg_rating,
        "in_stock_count": in_stock_count,
        "rating_distribution": rating_counts,
        "top_5_expensive": top_5_expensive,
        "top_5_affordable": top_5_affordable
    }

    with open(ANALYSIS_JSON, "w", encoding="utf-8") as f:
        json.dump(summary_results, f, indent=4)
    print(f"\nAnalysis summary saved to: {ANALYSIS_JSON.name}")
    return summary_results


def generate_visualizations(df: pd.DataFrame) -> None:
    """
    Generate professional, publication-ready Matplotlib charts.
    """
    print("\n" + "=" * 60)
    print("4. GENERATING MATPLOTLIB VISUALIZATIONS")
    print("=" * 60)

    # Set overall chart aesthetics
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8

    # -------------------------------------------------------------
    # Chart 1: Price Distribution (Histogram + KDE approximation)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    n, bins, patches = ax.hist(
        df["Price_Value"],
        bins=10,
        color="#2b5c8f",
        edgecolor="white",
        alpha=0.85
    )
    # Highlight mean line
    mean_val = df["Price_Value"].mean()
    ax.axvline(mean_val, color="#d9534f", linestyle="--", linewidth=2, label=f"Mean Price: £{mean_val:.2f}")

    ax.set_title("Distribution of Book Prices", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Price in GBP (£)", fontsize=11, labelpad=10)
    ax.set_ylabel("Number of Books", fontsize=11, labelpad=10)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc")

    chart_1_path = CHARTS_DIR / "price_distribution.png"
    plt.tight_layout()
    plt.savefig(chart_1_path, dpi=200)
    plt.close()
    print(f"Chart 1 saved: {chart_1_path.name}")

    # -------------------------------------------------------------
    # Chart 2: Rating Distribution Bar Chart
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    rating_counts = df["Rating_Score"].value_counts().sort_index()
    colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db"]

    bars = ax.bar(
        [f"{r} Star" for r in rating_counts.index],
        rating_counts.values,
        color=colors,
        edgecolor="#333333",
        linewidth=0.5,
        width=0.6
    )

    # Add data labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_title("Star Rating Distribution (1 to 5 Stars)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Star Rating", fontsize=11, labelpad=10)
    ax.set_ylabel("Book Count", fontsize=11, labelpad=10)
    ax.set_ylim(0, max(rating_counts.values) + 5)
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    chart_2_path = CHARTS_DIR / "rating_distribution.png"
    plt.tight_layout()
    plt.savefig(chart_2_path, dpi=200)
    plt.close()
    print(f"Chart 2 saved: {chart_2_path.name}")

    # -------------------------------------------------------------
    # Chart 3: Average Price by Star Rating
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    avg_price_rating = df.groupby("Rating_Score")["Price_Value"].mean().round(2)

    bars = ax.bar(
        [f"{r} Stars" for r in avg_price_rating.index],
        avg_price_rating.values,
        color="#16a085",
        edgecolor="#2c3e50",
        linewidth=0.5,
        width=0.55
    )

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"£{height:.2f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_title("Average Price across Star Ratings", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Star Rating", fontsize=11, labelpad=10)
    ax.set_ylabel("Average Price (£)", fontsize=11, labelpad=10)
    ax.set_ylim(0, max(avg_price_rating.values) + 10)
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    chart_3_path = CHARTS_DIR / "avg_price_by_rating.png"
    plt.tight_layout()
    plt.savefig(chart_3_path, dpi=200)
    plt.close()
    print(f"Chart 3 saved: {chart_3_path.name}")

    # -------------------------------------------------------------
    # Chart 4: Price Category Distribution (Donut Chart)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 6))
    cat_counts = df["Price_Category"].value_counts()[["Budget (<£25)", "Mid-Range (£25-£45)", "Premium (>£45)"]]
    donut_colors = ["#27ae60", "#2980b9", "#8e44ad"]

    wedges, texts, autotexts = ax.pie(
        cat_counts.values,
        labels=cat_counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=donut_colors,
        pctdistance=0.75,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(10)
        at.set_weight("bold")

    ax.set_title("Product Share by Price Category", fontsize=14, fontweight="bold", pad=20)
    chart_4_path = CHARTS_DIR / "price_category_share.png"
    plt.tight_layout()
    plt.savefig(chart_4_path, dpi=200)
    plt.close()
    print(f"Chart 4 saved: {chart_4_path.name}")


def export_cleaned_dataset(df: pd.DataFrame) -> None:
    """Save cleaned and transformed dataset to CSV."""
    df.to_csv(CLEANED_CSV, index=False, encoding="utf-8-sig")
    print(f"\nCleaned dataset exported to: {CLEANED_CSV}")


def main():
    print("\n" + "#" * 60)
    print(" DATHEON TASK 2: FULL DATA PROCESSING & ANALYSIS PIPELINE ")
    print("#" * 60)

    # 1. Load data
    df = load_data(INPUT_CSV)

    # 2. Clean and feature engineer
    df_clean = clean_and_transform(df)

    # 3. Statistical Analysis
    perform_statistical_analysis(df_clean)

    # 4. Visualizations
    generate_visualizations(df_clean)

    # 5. Export
    export_cleaned_dataset(df_clean)

    print("\n" + "=" * 60)
    print("TASK 2 EXECUTION COMPLETE & ALL DELIVERABLES GENERATED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
