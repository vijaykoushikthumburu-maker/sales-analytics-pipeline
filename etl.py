"""
etl.py
------
The Extract-Transform step of the pipeline.

- Extract: read the raw sales CSV.
- Transform: clean dirty values with pandas, then normalise the denormalised
  file into customers / products / orders tables (with surrogate keys).
"""

import pandas as pd

RAW_PATH = "data/raw_sales.csv"


def extract(path: str = RAW_PATH) -> pd.DataFrame:
    """Read the raw CSV into a DataFrame."""
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the raw rows: fix casing, handle blanks, drop duplicates, add revenue."""
    df = df.copy()

    # Normalise region: strip whitespace and standardise casing.
    df["region"] = df["region"].astype(str).str.strip().str.title()

    # Quantity may be blank -> treat missing as 1 (a single unit ordered).
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)

    # Types.
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    # Drop rows missing critical fields, then exact duplicates.
    df = df.dropna(subset=["order_id", "unit_price", "order_date"])
    df = df.drop_duplicates(subset=["order_id"])

    # Derived metric.
    df["revenue"] = df["unit_price"] * df["quantity"]

    return df


def normalise(df: pd.DataFrame):
    """
    Split the flat table into three related tables with surrogate keys:
    customers, products, orders.
    """
    # --- customers dimension ---
    customers = (
        df[["customer_name", "region"]]
        .drop_duplicates()
        .reset_index(drop=True)
        .reset_index()
        .rename(columns={"index": "customer_id"})
    )
    customers["customer_id"] += 1

    # --- products dimension ---
    products = (
        df[["product_name", "category", "unit_price"]]
        .drop_duplicates()
        .reset_index(drop=True)
        .reset_index()
        .rename(columns={"index": "product_id"})
    )
    products["product_id"] += 1

    # --- orders fact table (map names back to surrogate keys) ---
    orders = df.merge(customers, on=["customer_name", "region"]) \
               .merge(products, on=["product_name", "category", "unit_price"])
    orders = orders[["order_id", "customer_id", "product_id",
                     "quantity", "revenue", "order_date"]]
    orders["order_date"] = orders["order_date"].dt.strftime("%Y-%m-%d")

    return customers, products, orders


def run_etl(path: str = RAW_PATH):
    """Extract + transform, returning the three normalised DataFrames."""
    raw = extract(path)
    cleaned = clean(raw)
    customers, products, orders = normalise(cleaned)
    return customers, products, orders


if __name__ == "__main__":
    c, p, o = run_etl()
    print(f"customers: {len(c)} rows")
    print(f"products : {len(p)} rows")
    print(f"orders   : {len(o)} rows")
    print(o.head())
