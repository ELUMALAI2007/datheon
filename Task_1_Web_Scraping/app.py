from flask import Flask, render_template, send_file
import pandas as pd
from pathlib import Path

app = Flask(__name__)

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CSV_FILE = DATA_DIR / "scraped_data.csv"
JSON_FILE = DATA_DIR / "scraped_data.json"


def load_data():
    """Load scraped dataset from CSV into a Pandas DataFrame."""
    if CSV_FILE.exists():
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame()


@app.route("/")
def home():
    """Dashboard homepage with metrics, visualizations, and product table."""
    df = load_data()

    if df.empty:
        return "No data available. Run scraper.py first."

    # Summary metrics
    total_books = len(df)
    average_price = round(df["Price_Value"].mean(), 2)
    highest_price = round(df["Price_Value"].max(), 2)
    lowest_price = round(df["Price_Value"].min(), 2)

    # Rating distribution (counts for 1 to 5 stars)
    rating_counts = df["Rating_Score"].value_counts().to_dict()
    ratings_data = [rating_counts.get(i, 0) for i in range(1, 6)]

    # Price range distribution (£10-20, £20-30, £30-40, £40-50, £50-60)
    bins = [10, 20, 30, 40, 50, 60]
    labels = ["£10-£20", "£20-£30", "£30-£40", "£40-£50", "£50-£60"]
    price_series = pd.cut(df["Price_Value"], bins=bins, labels=labels, include_lowest=True)
    price_counts = price_series.value_counts()[labels].tolist()

    return render_template(
        "index.html",
        total_books=total_books,
        average_price=average_price,
        highest_price=highest_price,
        lowest_price=lowest_price,
        ratings_data=ratings_data,
        price_labels=labels,
        price_counts=price_counts,
        books=df.to_dict(orient="records")
    )


@app.route("/download/csv")
def download_csv():
    """Download scraped data as CSV."""
    return send_file(CSV_FILE, as_attachment=True, download_name="books_scraped.csv")


@app.route("/download/json")
def download_json():
    """Download scraped data as JSON."""
    return send_file(JSON_FILE, as_attachment=True, download_name="books_scraped.json")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
