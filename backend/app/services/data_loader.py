"""
Reads the Olist Kaggle CSVs from data/raw/ and loads them into PostgreSQL.
Usage: python -m app.services.data_loader

Expected files in data/raw/:
  olist_orders_dataset.csv
  olist_order_items_dataset.csv
  olist_customers_dataset.csv
  olist_products_dataset.csv
  olist_sellers_dataset.csv
  olist_order_reviews_dataset.csv
"""
import os
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from app.db.database import engine

# Path to raw CSVs (relative to project root)
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw"


def load_csv(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Missing: {path}\n"
            f"Download the Olist dataset from:\n"
            f"https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
        )
    print(f"  Loading {filename} ...")
    return pd.read_csv(path)


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    datetime_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df["freight_value"] = pd.to_numeric(df["freight_value"], errors="coerce").fillna(0)
    return df


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    # Reviews can have duplicate review_ids — keep first
    df = df.drop_duplicates(subset=["review_id"])
    for col in ["review_creation_date", "review_answer_timestamp"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_all():
    print("\n=== SmartCart Data Loader ===\n")

    with engine.connect() as conn:
        # Load in FK-safe order: customers → sellers → products → orders → items → reviews
        tables = [
            ("customers", "olist_customers_dataset.csv", None),
            ("sellers",   "olist_sellers_dataset.csv",   None),
            ("products",  "olist_products_dataset.csv",  None),
            ("orders",    "olist_orders_dataset.csv",    clean_orders),
            ("order_items","olist_order_items_dataset.csv", clean_order_items),
            ("order_reviews","olist_order_reviews_dataset.csv", clean_reviews),
        ]

        for table, filename, cleaner in tables:
            df = load_csv(filename)
            if cleaner:
                df = cleaner(df)

            # Truncate existing data so re-runs are safe
            conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            conn.commit()

            df.to_sql(table, con=conn, if_exists="append", index=False, method="multi", chunksize=1000)
            print(f"  ✓ {table}: {len(df):,} rows inserted")

    print("\n✅ All data loaded successfully!\n")


if __name__ == "__main__":
    load_all()