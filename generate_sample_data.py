"""
generate_sample_data.py
------------------------
Creates a realistic *raw* sales CSV (data/raw_sales.csv) with some intentional
messiness (inconsistent casing, a few blanks, duplicate rows) so the ETL step
has real cleaning to do.

Run:  python generate_sample_data.py
"""

import os
import csv
import random
from datetime import datetime, timedelta

REGIONS = ["North", "South", "East", "West"]

PRODUCTS = [
    # (product_name, category, unit_price)
    ("Wireless Mouse",      "Electronics", 799),
    ("Mechanical Keyboard", "Electronics", 2499),
    ("USB-C Hub",           "Electronics", 1599),
    ("Office Chair",        "Furniture",   6999),
    ("Standing Desk",       "Furniture",   14999),
    ("Desk Lamp",           "Furniture",   1299),
    ("Notebook Pack",       "Stationery",  299),
    ("Gel Pen Set",         "Stationery",  149),
    ("Water Bottle",        "Lifestyle",   499),
    ("Backpack",            "Lifestyle",   1999),
]

FIRST = ["Aarav", "Diya", "Vivaan", "Ananya", "Reyansh", "Ishaan", "Saanvi",
         "Kabir", "Myra", "Arjun", "Aadhya", "Vihaan"]
LAST = ["Sharma", "Verma", "Reddy", "Nair", "Iyer", "Gupta", "Patel", "Rao"]

OUTPUT = os.path.join("data", "raw_sales.csv")
NUM_ROWS = 2000


def messy_region(region: str) -> str:
    """Randomly distort casing/whitespace to simulate dirty source data."""
    roll = random.random()
    if roll < 0.15:
        return region.lower()
    if roll < 0.25:
        return f"  {region.upper()} "
    return region


def generate(num_rows: int = NUM_ROWS) -> None:
    os.makedirs("data", exist_ok=True)
    # Each customer has ONE fixed home region (realistic model).
    customers = [
        {"name": f"{random.choice(FIRST)} {random.choice(LAST)}",
         "region": random.choice(REGIONS)}
        for _ in range(120)
    ]
    start = datetime.now() - timedelta(days=365)

    rows = []
    for i in range(1, num_rows + 1):
        product_name, category, price = random.choice(PRODUCTS)
        order_date = start + timedelta(days=random.randint(0, 365))
        quantity = random.choice([1, 1, 1, 2, 2, 3, 4, ""])  # occasional blank
        customer = random.choice(customers)
        rows.append({
            "order_id": 100000 + i,
            "order_date": order_date.strftime("%Y-%m-%d"),
            "customer_name": customer["name"],
            "region": messy_region(customer["region"]),
            "product_name": product_name,
            "category": category,
            "unit_price": price,
            "quantity": quantity,
        })

    # Inject a few exact duplicate rows for the ETL to de-duplicate.
    rows.extend(random.sample(rows, 15))

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} raw sales rows to {OUTPUT}")


if __name__ == "__main__":
    generate()
