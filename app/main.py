import streamlit as st
import pandas as pd
import sys
import os

# Navigate to src to import our analytical engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.processor import clean_and_feature_engineer
from src.analytics import calculate_financial_health_score, get_monthly_summary

st.set_page_config(page_title="Personal Finance Intelligence", layout="wide")

st.title("💰 Financial Intelligence Dashboard")
st.markdown("### Welcome back! Here is your financial health at a glance.")

# 1. Load and Process Data
DATA_PATH = "data/raw/personal_expenses.csv"
PROCESSED_PATH = "data/processed/cleaned_expenses.csv"

# Ensure processed data is fresh
clean_and_feature_engineer(DATA_PATH, PROCESSED_PATH)
df = pd.read_csv(PROCESSED_PATH)

# 2. Sidebar Filters
st.sidebar.header("Filters")
month_list = df['month_name'].unique()
selected_month = st.sidebar.selectbox("Select Month", month_list)

# Filter data for calculations
monthly_df = df[df['month_name'] == selected_month]

# 3. Calculate Key Metrics using the Bridge Function
# This function handles the 3 required arguments internally
summary = get_monthly_summary(monthly_df)

# 4. Top-Level KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Income", f"₹{summary['total_income']:,.0f}")

with col2:
    st.metric("Total Expenses", f"₹{summary['total_spent']:,.0f}", delta_color="inverse")

with col3:
    # Calculate savings rate for the display
    savings_rate = (summary['savings'] / summary['total_income'] * 100) if summary['total_income'] > 0 else 0
    st.metric("Savings", f"₹{summary['savings']:,.0f}", delta=f"{savings_rate:.1f}% Rate")

with col4:
    # Now passing the health score and label we calculated in analytics.py
    st.metric("Financial Health", f"{summary['health_score']}/100", help=f"Status: {summary['health_label']}")

st.divider()

# Placeholder for next section
st.info("💡 Next: We will add the 'Spending Deep Dive' with interactive Plotly charts below these metrics.")

