"""
main.py — Personal Finance Intelligence (Multi-user edition)
Replace your existing app/main.py with this file entirely.

Changes from the original:
- Auth gate via auth_page.render_auth_page()
- All CSV reads/writes replaced with database calls
- Goals saved per-user in user_goals table
- Session state tracks logged-in user
"""

import streamlit as st
import pandas as pd
from datetime import date

# ── Bootstrap DB before anything else ────────────────────────────────────────
from src.database import init_db, get_transactions_df, add_transaction, import_csv_for_user, get_goals, save_goals
init_db()

# ── Auth gate ─────────────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.auth_page import render_auth_page

st.set_page_config(
    page_title="Personal Finance Intelligence",
    page_icon="💰",
    layout="wide",
)

if not render_auth_page():
    st.stop()   # Don't render anything else until logged in

# ── From here on, user is authenticated ──────────────────────────────────────
user    = st.session_state["user"]
user_id = user["id"]

# Sidebar: user info + logout
with st.sidebar:
    st.markdown(f"### 👤 {user['username']}")
    st.caption(user["email"])
    if st.button("Log Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def load_data(uid: int) -> pd.DataFrame:
    return get_transactions_df(uid)


# Processor still works — it just gets a DataFrame instead of reading a CSV
from src.processor import clean_and_feature_engineer
from src.analytics import compute_monthly_summary
from src.insights import generate_insights
from src.recommender import generate_recommendations

raw_df = load_data(user_id)

if raw_df.empty:
    processed_df = pd.DataFrame()
else:
    processed_df = clean_and_feature_engineer(raw_df.copy())

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_goals, tab_reco, tab_log, tab_import = st.tabs([
    "🎯 Goal Setup",
    "📊 Recommendations",
    "➕ Daily Log",
    "📁 Import CSV",
])

# ── Tab 1: Goal Setup ─────────────────────────────────────────────────────────
with tab_goals:
    st.header("Goal Setup")
    goals = get_goals(user_id)

    with st.form("goals_form"):
        salary     = st.number_input("Monthly Salary (₹)", min_value=0.0,
                                      value=float(goals["monthly_salary"]), step=1000.0)
        savings_pct = st.slider("Savings Target (%)", 0, 80,
                                 int(goals["savings_pct"]))
        if st.form_submit_button("Save Goals", use_container_width=True):
            save_goals(user_id, salary, savings_pct)
            st.success("Goals saved!")
            st.rerun()

    if goals["monthly_salary"] > 0:
        target = goals["monthly_salary"] * goals["savings_pct"] / 100
        st.info(f"🎯 Monthly savings target: **₹{target:,.0f}** "
                f"({goals['savings_pct']}% of ₹{goals['monthly_salary']:,.0f})")


# ── Tab 2: Recommendations ────────────────────────────────────────────────────
with tab_reco:
    st.header("Monthly Analysis & Recommendations")

    if processed_df.empty:
        st.warning("No transactions yet. Add some in the Daily Log tab or import a CSV.")
    else:
        goals      = get_goals(user_id)
        months     = sorted(processed_df["month_name"].unique(), reverse=True)
        chosen     = st.selectbox("Select Month", months)
        month_df   = processed_df[processed_df["month_name"] == chosen]
        summary    = compute_monthly_summary(
                         month_df,
                         income=goals["monthly_salary"],
                         savings_target_pct=goals["savings_pct"],
                     )
        insights   = generate_insights(summary)
        recs       = generate_recommendations(summary)

        # ── Metrics row ────────────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Spent",   f"₹{summary.get('total_spent', 0):,.0f}")
        col2.metric("Income",        f"₹{summary.get('income', 0):,.0f}")
        col3.metric("Saved",         f"₹{summary.get('savings', 0):,.0f}")
        col4.metric("Health Score",  f"{summary.get('health_score', 0):.0f}/100")

        st.divider()

        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("💡 Insights")
            for insight in insights:
                st.write(f"• {insight}")
        with col_r:
            st.subheader("🔧 Recommendations")
            for rec in recs:
                st.write(f"• {rec}")

        # ── Category breakdown chart ────────────────────────────────────────
        st.divider()
        st.subheader("Spending by Category")
        cat_data = (
            month_df.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        st.bar_chart(cat_data.set_index("category")["amount"])


# ── Tab 3: Daily Log ──────────────────────────────────────────────────────────
with tab_log:
    st.header("Log a Transaction")

    goals = get_goals(user_id)
    categories = [
        "Food & Dining", "Transport", "Shopping", "Entertainment",
        "Health", "Utilities", "Rent", "Education", "Travel", "Other",
    ]

    with st.form("log_form"):
        col1, col2 = st.columns(2)
        with col1:
            tx_date   = st.date_input("Date", value=date.today())
            amount    = st.number_input("Amount (₹)", min_value=0.01, step=10.0)
            category  = st.selectbox("Category", categories)
        with col2:
            description  = st.text_input("Description (optional)")
            payment_mode = st.selectbox("Payment Mode",
                                        ["UPI", "Card", "Cash", "Net Banking", "Other"])

        submitted = st.form_submit_button("Add Transaction", use_container_width=True)

    if submitted:
        add_transaction(
            user_id      = user_id,
            date         = str(tx_date),
            amount       = amount,
            category     = category,
            description  = description,
            payment_mode = payment_mode,
            income       = goals["monthly_salary"],
        )
        st.success(f"✅ Added ₹{amount:,.2f} in {category}.")
        st.cache_data.clear()
        st.rerun()


# ── Tab 4: Import CSV ─────────────────────────────────────────────────────────
with tab_import:
    st.header("Import Existing CSV")
    st.markdown(
        "Upload a CSV with columns: **date, amount, category** "
        "(and optionally *description, payment_mode, income*)."
    )

    uploaded = st.file_uploader("Choose CSV file", type=["csv"])

    if uploaded:
        # Save to a temp path then bulk-import
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name

        try:
            preview = pd.read_csv(tmp_path, nrows=5)
            st.dataframe(preview)
            if st.button("Confirm Import", use_container_width=True):
                import_csv_for_user(user_id, tmp_path)
                st.success("✅ CSV imported successfully!")
                st.cache_data.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
        finally:
            os.unlink(tmp_path)
