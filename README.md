# 🛒 Retail Sales Data Analytics Pipeline

An end-to-end **ETL pipeline** that ingests raw sales data, cleans and normalises
it with pandas, loads it into a relational SQL database, and reports on revenue,
products and customers through an interactive dashboard.

**🔗 Live demo:** _add your Streamlit Cloud link here after deploying_
**💻 Tech:** Python (pandas, NumPy) · SQL (SQLite / MySQL-compatible) · Streamlit · Plotly

---

## What it does

1. **Extract** – reads a raw, messy sales CSV (inconsistent casing, blank
   quantities, duplicate rows).
2. **Transform** – with pandas: standardises regions, fills/validates missing
   values, removes duplicates, computes revenue, and normalises the flat file
   into **customers / products / orders** tables with surrogate keys.
3. **Load** – writes the three related tables into SQLite (with primary &
   foreign keys).
4. **Analyse** – runs SQL reports and renders them in a dashboard.

### Analytical SQL on show
- Monthly revenue with a **running cumulative total** (`SUM() OVER (...)`)
- **Month-over-month growth** using `LAG()`
- Top products and revenue by category/region (multi-table **JOINs**)
- Highest-spending customers ranked with `RANK()` inside a **CTE**

---

## Project structure

```
sales-analytics-pipeline/
├── generate_sample_data.py   # creates a realistic, slightly messy raw CSV
├── etl.py                    # extract + clean + normalise (pandas)
├── database.py               # schema, loading, and analytical SQL
├── pipeline.py               # generate -> ETL -> load
├── app.py                    # Streamlit dashboard
├── requirements.txt
└── README.md
```

---

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python pipeline.py      # build the database from sample data
streamlit run app.py    # launch the dashboard at http://localhost:8501
```

---

## Deploy a live link (free)

1. Push this folder to a **public GitHub repository**.
2. Go to **share.streamlit.io**, sign in with GitHub, **New app**.
3. Pick the repo and set the main file to `app.py`.
4. Copy the public URL Streamlit gives you into the **Live demo** line above
   and onto your resume.

---

## Using MySQL instead of SQLite

The SQL is standard and runs on **MySQL 8+** with two small changes:
- swap the `sqlite3` connection in `database.py` for `mysql-connector-python`
- replace `strftime('%Y-%m', order_date)` with `DATE_FORMAT(order_date, '%Y-%m')`

---

## What I learned / can explain

- Building a real ETL flow: extract, clean, normalise, load
- Data cleaning with pandas (types, missing values, duplicates, text normalisation)
- Designing a small relational schema with primary/foreign keys
- Analytical SQL: joins, aggregation, CTEs and window functions (`SUM OVER`, `LAG`, `RANK`)
