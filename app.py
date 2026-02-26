import streamlit as st
import pandas as pd
import plotly.express as px

# STEP 2 — Page Config
st.set_page_config(layout="wide")
st.title("NovaRetail Customer Intelligence Dashboard")
st.subheader("Customer Behavior and Revenue Analysis")

# STEP 3 — Load Data
try:
    df = pd.read_excel("NR_dataset.xlsx")
except Exception:
    st.error("Dataset file not found in repository.")
    st.stop()

# Normalize all column names
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

# Validate required fields
required_cols = [
    'label', 'customerid', 'transactionid', 'transactiondate',
    'productcategory', 'purchaseamount', 'customeragegroup',
    'customergender', 'customerregion', 'customersatisfaction',
    'retailchannel'
]

missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    st.error(f"Missing logical fields: {', '.join(missing_cols)}")
    st.write(df.columns)
    st.stop()

# Type conversions
df['purchaseamount'] = pd.to_numeric(df['purchaseamount'], errors='coerce')
df['customersatisfaction'] = pd.to_numeric(df['customersatisfaction'], errors='coerce')
df['transactiondate'] = pd.to_datetime(df['transactiondate'], errors='coerce')

# Drop rows with missing purchaseamount
df = df.dropna(subset=['purchaseamount'])

# STEP 4 — Sidebar Filters
st.sidebar.header("Filters")

def get_filter_options(col_name):
    opts = df[col_name].dropna().unique().tolist()
    return ["All"] + sorted(opts)

filter_label = st.sidebar.multiselect("Customer Segment", get_filter_options('label'), default=["All"])
filter_region = st.sidebar.multiselect("Customer Region", get_filter_options('customerregion'), default=["All"])
filter_category = st.sidebar.multiselect("Product Category", get_filter_options('productcategory'), default=["All"])
filter_channel = st.sidebar.multiselect("Retail Channel", get_filter_options('retailchannel'), default=["All"])
filter_age = st.sidebar.multiselect("Customer Age Group", get_filter_options('customeragegroup'), default=["All"])

# Date filter handling
min_date = df['transactiondate'].min()
max_date = df['transactiondate'].max()

if pd.notna(min_date) and pd.notna(max_date):
    date_filter = st.sidebar.date_input("Date Range", [min_date.date(), max_date.date()])
else:
    date_filter = []

# STEP 5 — Filtering Logic
df_filtered = df.copy()

if "All" not in filter_label and filter_label:
    df_filtered = df_filtered[df_filtered['label'].isin(filter_label)]
if "All" not in filter_region and filter_region:
    df_filtered = df_filtered[df_filtered['customerregion'].isin(filter_region)]
if "All" not in filter_category and filter_category:
    df_filtered = df_filtered[df_filtered['productcategory'].isin(filter_category)]
if "All" not in filter_channel and filter_channel:
    df_filtered = df_filtered[df_filtered['retailchannel'].isin(filter_channel)]
if "All" not in filter_age and filter_age:
    df_filtered = df_filtered[df_filtered['customeragegroup'].isin(filter_age)]

if len(date_filter) == 2:
    start_date, end_date = date_filter
    df_filtered = df_filtered[
        (df_filtered['transactiondate'].dt.date >= start_date) &
        (df_filtered['transactiondate'].dt.date <= end_date)
    ]

# STEP 10 — Edge Case Handling (Empty state)
if df_filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

# STEP 6 — KPI Calculations
total_revenue = df_filtered['purchaseamount'].sum()
total_transactions = len(df_filtered)
avg_satisfaction = df_filtered['customersatisfaction'].mean()

segment_revenue = df_filtered.groupby('label')['purchaseamount'].sum()
top_segment = segment_revenue.idxmax() if not segment_revenue.empty else "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Total Transactions", total_transactions)
col3.metric("Avg Customer Satisfaction", f"{avg_satisfaction:.2f}" if pd.notna(avg_satisfaction) else "N/A")
col4.metric("Top Revenue Segment", top_segment)

# STEP 7 — Aggregations
rev_by_segment = df_filtered.groupby('label', as_index=False)['purchaseamount'].sum()
rev_by_category = df_filtered.groupby('productcategory', as_index=False)['purchaseamount'].sum()
rev_by_region = df_filtered.groupby('customerregion', as_index=False)['purchaseamount'].sum()

# Explicit column for date grouping to avoid pandas edge case errors
df_filtered['transaction_date_only'] = df_filtered['transactiondate'].dt.date
rev_by_date = df_filtered.groupby('transaction_date_only', as_index=False)['purchaseamount'].sum()

# STEP 8 — Visualizations
c1, c2 = st.columns(2)
with c1:
    fig1 = px.bar(rev_by_segment, x='label', y='purchaseamount', title="Revenue by Customer Segment")
    st.plotly_chart(fig1, use_container_width=True)
with c2:
    fig2 = px.bar(rev_by_category, x='productcategory', y='purchaseamount', title="Revenue by Product Category")
    st.plotly_chart(fig2, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    fig3 = px.bar(rev_by_region, x='customerregion', y='purchaseamount', title="Revenue by Region")
    st.plotly_chart(fig3, use_container_width=True)
with c4:
    fig4 = px.pie(df_filtered, values='purchaseamount', names='retailchannel', title="Sales Channel Distribution")
    st.plotly_chart(fig4, use_container_width=True)

c5, c6 = st.columns(2)
with c5:
    fig5 = px.box(df_filtered, x='label', y='customersatisfaction', title="Customer Satisfaction by Segment")
    st.plotly_chart(fig5, use_container_width=True)
with c6:
    fig6 = px.line(rev_by_date, x='transaction_date_only', y='purchaseamount', title="Revenue Trend Over Time")
    st.plotly_chart(fig6, use_container_width=True)

# STEP 9 — Show Filtered Table
df_display = df_filtered.drop(columns=['transaction_date_only'], errors='ignore')
st.dataframe(df_display, hide_index=True, use_container_width=True)
