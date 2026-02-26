import streamlit as st
import pandas as pd
import plotly.express as px

# STEP 2 — Page Config
st.set_page_config(layout="wide")
st.title("NovaRetail Customer Intelligence Dashboard")
st.subheader("Customer Behavior and Revenue Analysis")

# STEP 3 — Load Data
@st.cache_data
def load_and_preprocess_data():
    try:
        df = pd.read_excel("NR_dataset.xlsx")
    except FileNotFoundError:
        st.error("Dataset file not found in repository.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        st.stop()

    # Normalize all column names: strip whitespace, lower, replace space with underscore
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    # Expected logical fields
    required_fields = [
        "label", "customerid", "transactionid", "transactiondate", 
        "productcategory", "purchaseamount", "customeragegroup", 
        "customergender", "customerregion", "customersatisfaction", 
        "retailchannel"
    ]

    # Validate required fields
    missing_fields = [col for col in required_fields if col not in df.columns]
    if missing_fields:
        st.error(f"Missing required logical fields: {', '.join(missing_fields)}")
        st.write("Actual columns in the dataset:")
        st.write(list(df.columns))
        st.stop()

    # Convert specific columns
    df['purchaseamount'] = pd.to_numeric(df['purchaseamount'], errors='coerce')
    df['customersatisfaction'] = pd.to_numeric(df['customersatisfaction'], errors='coerce')
    df['transactiondate'] = pd.to_datetime(df['transactiondate'], errors='coerce')

    # Drop rows with missing purchaseamount
    df = df.dropna(subset=['purchaseamount'])

    return df

df_raw = load_and_preprocess_data()

# STEP 4 — Sidebar Filters
st.sidebar.header("Filters")

def create_multiselect(label_name, column_name):
    unique_vals = sorted(df_raw[column_name].dropna().unique().tolist())
    options = ["All"] + unique_vals
    return st.sidebar.multiselect(label_name, options, default=["All"])

filter_segment = create_multiselect("Customer Segment", "label")
filter_region = create_multiselect("Customer Region", "customerregion")
filter_category = create_multiselect("Product Category", "productcategory")
filter_channel = create_multiselect("Retail Channel", "retailchannel")
filter_age = create_multiselect("Customer Age Group", "customeragegroup")

# Date Range Filter
min_date = df_raw['transactiondate'].min()
max_date = df_raw['transactiondate'].max()

if pd.notnull(min_date) and pd.notnull(max_date):
    min_date_val = min_date.date()
    max_date_val = max_date.date()
    date_range = st.sidebar.date_input("Date Range", [min_date_val, max_date_val], min_value=min_date_val, max_value=max_date_val)
else:
    date_range = []

# STEP 5 — Filtering Logic
df_filtered = df_raw.copy()

if "All" not in filter_segment and filter_segment:
    df_filtered = df_filtered[df_filtered['label'].isin(filter_segment)]
if "All" not in filter_region and filter_region:
    df_filtered = df_filtered[df_filtered['customerregion'].isin(filter_region)]
if "All" not in filter_category and filter_category:
    df_filtered = df_filtered[df_filtered['productcategory'].isin(filter_category)]
if "All" not in filter_channel and filter_channel:
    df_filtered = df_filtered[df_filtered['retailchannel'].isin(filter_channel)]
if "All" not in filter_age and filter_age:
    df_filtered = df_filtered[df_filtered['customeragegroup'].isin(filter_age)]

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_filtered[
        (df_filtered['transactiondate'].dt.date >= start_date) & 
        (df_filtered['transactiondate'].dt.date <= end_date)
    ]

# Edge Case Handling: Empty filter result
if df_filtered.empty:
    st.warning("No data matches the selected filters. Please adjust your criteria.")
    st.stop()

# STEP 6 — KPI Calculations
total_revenue = df_filtered['purchaseamount'].sum()
total_transactions = len(df_filtered)
avg_satisfaction = df_filtered['customersatisfaction'].mean()

top_segment_series = df_filtered.groupby('label')['purchaseamount'].sum()
top_segment = top_segment_series.idxmax() if not top_segment_series.empty else "N/A"

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Revenue", f"${total_revenue:,.2f}")
kpi2.metric("Total Transactions", f"{total_transactions:,}")
kpi3.metric("Avg Customer Satisfaction", f"{avg_satisfaction:.2f}" if pd.notnull(avg_satisfaction) else "N/A")
kpi4.metric("Top Revenue Segment", str(top_segment))

st.markdown("---")

# STEP 7 & 8 — Aggregations and Visualizations
col1, col2 = st.columns(2)

with col1:
    # Chart 1 — Revenue by Segment
    rev_by_segment = df_filtered.groupby('label', as_index=False)['purchaseamount'].sum()
    fig1 = px.bar(rev_by_segment, x='label', y='purchaseamount', title="Revenue by Customer Segment")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Chart 2 — Revenue by Product Category
    rev_by_category = df_filtered.groupby('productcategory', as_index=False)['purchaseamount'].sum()
    fig2 = px.bar(rev_by_category, x='productcategory', y='purchaseamount', title="Revenue by Product Category")
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    # Chart 3 — Revenue by Region
    rev_by_region = df_filtered.groupby('customerregion', as_index=False)['purchaseamount'].sum()
    fig3 = px.bar(rev_by_region, x='customerregion', y='purchaseamount', title="Revenue by Region")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    # Chart 4 — Sales Channel Distribution
    fig4 = px.pie(df_filtered, values='purchaseamount', names='retailchannel', title="Sales Channel Distribution")
    st.plotly_chart(fig4, use_container_width=True)

col5, col6 = st.columns(2)

with col5:
    # Chart 5 — Customer Satisfaction by Segment
    fig5 = px.box(df_filtered, x='label', y='customersatisfaction', title="Customer Satisfaction by Segment")
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    # Chart 6 — Revenue Trend
    # Create an aggregated dataset for revenue by date
    rev_by_date = df_filtered.groupby(df_filtered['transactiondate'].dt.date, as_index=False)['purchaseamount'].sum()
    # Rename column to maintain consistency for Plotly Express
    rev_by_date.rename(columns={'transactiondate': 'date'}, inplace=True)
    fig6 = px.line(rev_by_date, x='date', y='purchaseamount', title="Revenue Trend Over Time")
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# STEP 9 — Show Filtered Table
st.subheader("Filtered Dataset")
st.dataframe(df_filtered, hide_index=True, use_container_width=True)
