"""
pipeline.py
-----------
End-to-end pipeline: generate raw data (if missing) -> ETL -> load to SQLite.

Run once before launching the dashboard:
    python pipeline.py
"""

import os

import generate_sample_data
import etl
import database


def run() -> None:
    # 1. Ensure raw source data exists.
    if not os.path.exists(etl.RAW_PATH):
        print("No raw data found - generating sample sales data...")
        generate_sample_data.generate()

    # 2. Extract + transform.
    print("Running ETL (extract -> clean -> normalise)...")
    customers, products, orders = etl.run_etl()
    print(f"  -> {len(customers)} customers, {len(products)} products, "
          f"{len(orders)} orders")

    # 3. Load into the database.
    print("Loading into SQLite...")
    conn = database.get_connection()
    database.create_schema(conn)
    database.load(conn, customers, products, orders)

    # 4. Sanity check.
    m = database.overview_metrics(conn)
    conn.close()
    print(f"Done. Total revenue ₹{m['total_revenue']:,.0f} across "
          f"{m['total_orders']} orders from {m['customers']} customers.")


if __name__ == "__main__":
    run()
