"""
database.py
-----------
Loads the normalised data into SQLite and provides the analytical SQL queries
used by the dashboard.

The SQL (joins, GROUP BY, CTEs, window functions) is standard and runs on
MySQL 8+ with only minor date-function changes (noted in comments).
"""

import os
import sqlite3

import pandas as pd

DB_PATH = "sales.db"


def get_connection(db_path: str = DB_PATH):
    return sqlite3.connect(db_path)


def is_ready(db_path: str = DB_PATH) -> bool:
    """True when the database file exists and has loaded order data."""
    if not os.path.exists(db_path):
        return False
    try:
        conn = get_connection(db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            return count > 0
        finally:
            conn.close()
    except sqlite3.Error:
        return False


def create_schema(conn) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS products;

        CREATE TABLE customers (
            customer_id   INTEGER PRIMARY KEY,
            customer_name TEXT,
            region        TEXT
        );

        CREATE TABLE products (
            product_id   INTEGER PRIMARY KEY,
            product_name TEXT,
            category     TEXT,
            unit_price   REAL
        );

        CREATE TABLE orders (
            order_id    INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(customer_id),
            product_id  INTEGER REFERENCES products(product_id),
            quantity    INTEGER,
            revenue     REAL,
            order_date  TEXT
        );
        """
    )
    conn.commit()


def _insert_df(conn, table: str, df: pd.DataFrame) -> None:
    """Insert rows with sqlite3 directly (avoids pandas to_sql backend issues)."""
    cols = ", ".join(df.columns)
    placeholders = ", ".join("?" for _ in df.columns)
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    rows = [tuple(row) for row in df.itertuples(index=False, name=None)]
    conn.executemany(sql, rows)


def load(conn, customers, products, orders) -> None:
    _insert_df(conn, "customers", customers)
    _insert_df(conn, "products", products)
    _insert_df(conn, "orders", orders)
    conn.commit()


# ----------------------------------------------------------------------------
# Analytical queries — each returns a pandas DataFrame.
# ----------------------------------------------------------------------------

def monthly_revenue(conn) -> pd.DataFrame:
    """
    Revenue per month with a running cumulative total (WINDOW function).
    SQLite uses strftime(); MySQL uses DATE_FORMAT(order_date, '%Y-%m').
    """
    return pd.read_sql_query(
        """
        WITH monthly AS (
            SELECT strftime('%Y-%m', order_date) AS month,
                   SUM(revenue)                  AS revenue
            FROM   orders
            GROUP  BY month
        )
        SELECT month,
               revenue,
               SUM(revenue) OVER (ORDER BY month) AS cumulative_revenue
        FROM   monthly
        ORDER  BY month
        """,
        conn,
    )


def revenue_growth(conn) -> pd.DataFrame:
    """Month-over-month growth using LAG()."""
    return pd.read_sql_query(
        """
        WITH monthly AS (
            SELECT strftime('%Y-%m', order_date) AS month,
                   SUM(revenue)                  AS revenue
            FROM   orders
            GROUP  BY month
        )
        SELECT month,
               revenue,
               LAG(revenue) OVER (ORDER BY month) AS prev_revenue,
               ROUND(
                   100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
                   / LAG(revenue) OVER (ORDER BY month), 1
               ) AS growth_pct
        FROM   monthly
        ORDER  BY month
        """,
        conn,
    )


def top_products(conn, limit: int = 10) -> pd.DataFrame:
    """Best-selling products by revenue (JOIN orders -> products)."""
    return pd.read_sql_query(
        f"""
        SELECT   p.product_name,
                 p.category,
                 SUM(o.quantity) AS units_sold,
                 SUM(o.revenue)  AS revenue
        FROM     orders   o
        JOIN     products p ON o.product_id = p.product_id
        GROUP BY p.product_name, p.category
        ORDER BY revenue DESC
        LIMIT    {int(limit)}
        """,
        conn,
    )


def revenue_by_region(conn) -> pd.DataFrame:
    """Revenue split by customer region (JOIN orders -> customers)."""
    return pd.read_sql_query(
        """
        SELECT   c.region,
                 COUNT(DISTINCT o.order_id) AS orders,
                 SUM(o.revenue)             AS revenue
        FROM     orders    o
        JOIN     customers c ON o.customer_id = c.customer_id
        GROUP BY c.region
        ORDER BY revenue DESC
        """,
        conn,
    )


def revenue_by_category(conn) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT   p.category,
                 SUM(o.revenue) AS revenue
        FROM     orders   o
        JOIN     products p ON o.product_id = p.product_id
        GROUP BY p.category
        ORDER BY revenue DESC
        """,
        conn,
    )


def top_customers(conn, limit: int = 10) -> pd.DataFrame:
    """Highest-spending customers, ranked with a WINDOW function inside a CTE."""
    return pd.read_sql_query(
        f"""
        WITH customer_spend AS (
            SELECT   c.customer_name,
                     c.region,
                     SUM(o.revenue) AS total_spend
            FROM     orders    o
            JOIN     customers c ON o.customer_id = c.customer_id
            GROUP BY c.customer_name, c.region
        )
        SELECT customer_name,
               region,
               total_spend,
               RANK() OVER (ORDER BY total_spend DESC) AS spend_rank
        FROM   customer_spend
        ORDER  BY total_spend DESC
        LIMIT  {int(limit)}
        """,
        conn,
    )


def overview_metrics(conn) -> dict:
    df = pd.read_sql_query(
        """
        SELECT SUM(revenue)               AS total_revenue,
               COUNT(*)                   AS total_orders,
               COUNT(DISTINCT customer_id) AS customers,
               AVG(revenue)               AS avg_order_value
        FROM orders
        """,
        conn,
    )
    row = df.iloc[0]
    return {
        "total_revenue": float(row["total_revenue"]),
        "total_orders": int(row["total_orders"]),
        "customers": int(row["customers"]),
        "avg_order_value": float(row["avg_order_value"]),
    }
