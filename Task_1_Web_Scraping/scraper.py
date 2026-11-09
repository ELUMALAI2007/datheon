# ============================================
# DATHEON INTERNSHIP - TASK 1
# WEB SCRAPING AND DATA EXTRACTION
# ============================================

# Import required libraries
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path


# ============================================
# 1. PROJECT CONFIGURATION
# ============================================

# Project directory
BASE_DIR = Path(__file__).resolve().parent

# Data directory
DATA_DIR = BASE_DIR / "data"

# Create data directory automatically
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Website URL
START_URL = "https://books.toscrape.com/"

# Maximum records to extract
MAX_RECORDS = 100


# ============================================
# 2. REQUEST SESSION
# ============================================

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; EducationalScraper/1.0)"
})


# ============================================
# 3. WEB SCRAPING FUNCTION
# ============================================

def scrape_books():
    all_books = []
    current_url = START_URL
    page_number = 1

    print("\n================================")
    print("   DATHEON WEB SCRAPING STARTED")
    print("================================")

    while current_url and len(all_books) < MAX_RECORDS:
        print(f"\nScraping Page {page_number}...")

        try:
            # Send HTTP request
            response = session.get(current_url, timeout=15)

            # Check HTTP response
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all book elements
            books = soup.find_all("article", class_="product_pod")

            # Extract book information
            for book in books:
                title = book.h3.a["title"]

                price = book.find("p", class_="price_color").get_text(strip=True)

                rating = book.find("p", class_="star-rating")["class"][1]

                availability = book.find("p", class_="instock availability").get_text(strip=True)

                # Get individual book URL
                book_url = urljoin(current_url, book.h3.a["href"])

                # Store extracted information
                book_data = {
                    "Title": title,
                    "Price": price,
                    "Rating": rating,
                    "Availability": availability,
                    "URL": book_url,
                    "Page": page_number
                }

                all_books.append(book_data)

                # Stop after reaching 100 records
                if len(all_books) >= MAX_RECORDS:
                    break

            print("Total Books Collected:", len(all_books))

            # Find next page
            next_page = soup.select_one("li.next a")

            if next_page and len(all_books) < MAX_RECORDS:
                current_url = urljoin(current_url, next_page["href"])
                page_number += 1
            else:
                current_url = None

        except requests.RequestException as error:
            print("\nWebsite Connection Error:", error)
            break

        except (AttributeError, KeyError, IndexError) as error:
            print("\nData Extraction Error:", error)
            break

    return all_books


# ============================================
# 4. DATA PROCESSING USING PANDAS
# ============================================

def process_data(all_books):
    if not all_books:
        print("\nNo records available for processing.")
        return None

    # Convert Python list into DataFrame
    df = pd.DataFrame(all_books)

    print("\n================================")
    print("       DATA PROCESSING")
    print("================================")

    # Display first five records
    print("\nFirst Five Records:")
    print(df.head())

    # Dataset information
    print("\nDataset Information:")
    df.info()

    # Total records
    print("\nTotal Records:", len(df))

    # Column names
    print("\nColumn Names:")
    print(df.columns.tolist())

    return df


# ============================================
# 5. DATA CLEANING AND VALIDATION
# ============================================

def clean_data(df):
    print("\n========== DATA CLEANING ==========")

    # 1. Check missing values
    print("\nMissing Values Before Cleaning:")
    print(df.isnull().sum())

    # 2. Remove duplicate records
    df = df.drop_duplicates(subset=["Title"])
    print("\nDuplicate Records Removed")

    # 3. Remove records without essential information
    df = df.dropna(subset=["Title", "Price", "Rating"])

    # 4. Convert price into numeric format (extract float, remove currency symbol)
    df["Price_Value"] = pd.to_numeric(
        df["Price"].str.replace("£", "", regex=False),
        errors="coerce"
    )

    # 5. Convert ratings into numerical values
    rating_mapping = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    df["Rating_Score"] = df["Rating"].map(rating_mapping)

    # 6. Remove invalid price or rating records
    df = df.dropna(subset=["Price_Value", "Rating_Score"])

    # 7. Reset row indexes
    df = df.reset_index(drop=True)

    # 8. Validate final dataset
    print("\nMissing Values After Cleaning:")
    print(df.isnull().sum())

    print("\nFinal Dataset Information:")
    print("Total Records:", len(df))
    print("Duplicate Records:", df.duplicated(subset=["Title"]).sum())
    print("Invalid Prices:", df["Price_Value"].isna().sum())

    print("\nData Cleaning Completed Successfully!")
    return df


# ============================================
# 6. EXPORT DATA INTO CSV AND JSON
# ============================================

def export_data(df):
    if df is None:
        return

    print("\n================================")
    print("         DATA EXPORT")
    print("================================")

    # CSV file path
    csv_file = DATA_DIR / "scraped_data.csv"

    # Export CSV
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    print("\nCSV Export Successful!")
    print("Location:", csv_file)

    # JSON file path
    json_file = DATA_DIR / "scraped_data.json"

    # Export JSON
    df.to_json(json_file, orient="records", indent=4, force_ascii=False)
    print("\nJSON Export Successful!")
    print("Location:", json_file)


# ============================================
# 7. MAIN PROGRAM
# ============================================

def main():
    # Step 1: Scrape website
    books = scrape_books()

    # Step 2: Convert into DataFrame
    df = process_data(books)

    if df is None:
        return

    # Step 3: Clean dataset
    df = clean_data(df)

    # Step 4: Export cleaned data
    export_data(df)

    print("\n================================")
    print("       FINAL SUMMARY")
    print("================================")
    print("Total Clean Records:", len(df))
    print("\nDATHEON TASK 1 COMPLETED!")


if __name__ == "__main__":
    main()

