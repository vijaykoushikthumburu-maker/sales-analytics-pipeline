"""
app.py
------
Interactive Streamlit dashboard for the retail sales analytics pipeline.

Run locally:   streamlit run app.py
Deploy free:   push to GitHub, then share.streamlit.io -> point at this file.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import database
import pipeline

st.set_page_config(page_title="Retail Sales Analytics", page_icon="🛒", layout="wide")

# Build the database on first run (useful for cloud deployment).
if not database.is_ready():
    with st.spinner("Setting up sample data for the first time..."):
        pipeline.run()


@st.cache_data
def load_all():
    conn = database.get_connection()
    data = {
        "metrics": database.overview_metrics(conn),
        "monthly": database.monthly_revenue(conn),
        "growth": database.revenue_growth(conn),
        "products": database.top_products(conn),
        "region": database.revenue_by_region(conn),
        "category": database.revenue_by_category(conn),
        "customers": database.top_customers(conn),
    }
    conn.close()
    return data


data = load_all()

st.title("🛒 Retail Sales Data Analytics")
st.caption("An ETL pipeline that cleans raw sales data, loads it into a "
           "relational SQL database, and reports on revenue, products and customers.")

# ---- KPI cards ----
m = data["metrics"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total revenue", f"₹{m['total_revenue']:,.0f}")
c2.metric("Orders", f"{m['total_orders']:,}")
c3.metric("Customers", f"{m['customers']:,}")
c4.metric("Avg order value", f"₹{m['avg_order_value']:,.0f}")

st.divider()

# ---- Revenue trend + cumulative ----
st.subheader("Monthly revenue & cumulative total")
monthly = data["monthly"]
fig = px.bar(monthly, x="month", y="revenue", labels={"revenue": "monthly revenue"})
fig.add_scatter(x=monthly["month"], y=monthly["cumulative_revenue"],
                name="cumulative", mode="lines+markers", yaxis="y2")
fig.update_layout(yaxis2=dict(overlaying="y", side="right", title="cumulative"))
st.plotly_chart(fig, width='stretch')

# ---- Region + category ----
left, right = st.columns(2)
with left:
    st.subheader("Revenue by region")
    fig = px.bar(data["region"], x="region", y="revenue", color="revenue",
                 color_continuous_scale="Blues")
    st.plotly_chart(fig, width='stretch')
with right:
    st.subheader("Revenue by category")
    fig = px.pie(data["category"], names="category", values="revenue", hole=0.45)
    st.plotly_chart(fig, width='stretch')

# ---- Top products ----
st.subheader("Top products by revenue")
fig = px.bar(data["products"], x="revenue", y="product_name", color="category",
             orientation="h")
fig.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig, width='stretch')

# ---- Tables: growth + top customers ----
left, right = st.columns(2)
with left:
    st.subheader("Month-over-month growth")
    st.dataframe(data["growth"], width='stretch', hide_index=True)
with right:
    st.subheader("Top customers")
    st.dataframe(data["customers"], width='stretch', hide_index=True)

st.caption("Built with Python (pandas, NumPy), SQL and Streamlit.")
