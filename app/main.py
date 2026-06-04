"""
main.py — Personal Finance Intelligence (Multi-user edition)
"""

import streamlit as st
import pandas as pd
from datetime import date
import sys
from pathlib import Path
import plotly.express as px

# ── Add project root to path ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Bootstrap DB before anything else ────────────────────────────────────────
from src.database import init_db, get_transactions_df, add_transaction, import_csv_for_user, get_goals, save_goals
from app.auth_page import render_auth_page

init_db()

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

# ── Plotly styling with enhanced contrast ────────────────────────────────────
# Background: darker for better white text contrast
_PLOT_PANEL_BG = "#1a1f2e"
_PLOT_PANEL_BORDER = "#4a7c99"
_PLOT_HOVERLABEL = dict(
    bgcolor=_PLOT_PANEL_BG,
    bordercolor=_PLOT_PANEL_BORDER,
    align="left",
    font=dict(color="#ffffff", size=13, family="Arial, sans-serif"),
    namelength=-1,  # Show full text in hover
)
_PLOT_LEGEND = dict(
    bgcolor=_PLOT_PANEL_BG,
    bordercolor=_PLOT_PANEL_BORDER,
    font=dict(color="#e8f0f8", size=11, family="Arial, sans-serif"),
    tracegroupgap=8,
    x=0.02,
    y=0.98,
    xanchor="left",
    yanchor="top",
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def load_data(uid: int) -> pd.DataFrame:
    return get_transactions_df(uid)


# Processor still works — it just gets a DataFrame instead of reading a CSV
from src.processor import clean_and_feature_engineer
from src.analytics import get_monthly_summary
from src.insights import generate_automated_insights
from src.recommender import get_recommendations

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
        summary    = get_monthly_summary(
                         month_df,
                         monthly_income_override=goals["monthly_salary"],
                         savings_goal_pct=goals["savings_pct"],
                     )
        
        # Generate insights and recommendations
        try:
            insights   = generate_automated_insights(summary)
        except:
            insights = []
        
        try:
            recs       = get_recommendations(summary)
        except:
            recs = []

        # ── Metrics row ────────────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Spent",   f"₹{summary.get('total_spent', 0):,.0f}")
        col2.metric("Income",        f"₹{summary.get('total_income', 0):,.0f}")
        col3.metric("Saved",         f"₹{summary.get('savings', 0):,.0f}")
        col4.metric("Health Score",  f"{summary.get('health_score', 0):.0f}/100")

        st.divider()

        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("💡 Insights")
            if insights:
                for insight in insights:
                    st.write(f"• {insight}")
            else:
                st.info("No insights available yet.")
        with col_r:
            st.subheader("🔧 Recommendations")
            if recs:
                for rec in recs:
                    st.write(f"• {rec}")
            else:
                st.info("No recommendations available yet.")

        # ── Spending Deep Dive - Plotly Charts ──────────────────────────────
        st.divider()
        st.markdown("#### 📈 Spending Deep Dive")
        
        category_data = summary.get("category_shares", {})
        
        if category_data:
            # 1. Donut Chart - Spending Distribution
            fig_pie = px.pie(
                names=list(category_data.keys()),
                values=list(category_data.values()),
                hole=0.4,
                title=f"Spending Distribution: {chosen}",
                template="plotly_dark"
            )
            fig_pie.update_traces(
                textposition="inside",
                textfont=dict(size=12, color="#ffffff"),
                hovertemplate="<b>%{label}</b><br>₹%{value:.0f} (%{percent})<extra></extra>"
            )
            fig_pie.update_layout(
                hoverlabel=_PLOT_HOVERLABEL,
                legend=_PLOT_LEGEND,
                font=dict(color="#e8f0f8", size=12),
                title_font=dict(size=16, color="#e8f0f8"),
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            # 2. Line Chart - Cumulative Spending Trend
            if not month_df.empty:
                burn_df = month_df.sort_values("date")
                fig_burn = px.line(
                    burn_df,
                    x="date",
                    y="cumulative_spent",
                    title=f"Cumulative Spending Trend: {chosen}",
                    labels={"cumulative_spent": "Total Spent (₹)", "date": "Date"},
                    template="plotly_dark"
                )
                fig_burn.update_traces(
                    line=dict(color="#4a7c99", width=3),
                    hovertemplate="<b>Date:</b> %{x|%d-%b-%Y}<br><b>Cumulative:</b> ₹%{y:.0f}<extra></extra>"
                )
                fig_burn.add_hline(
                    y=summary.get("total_income", 0),
                    line_dash="dash",
                    line_color="#ff6b6b",
                    line_width=2,
                    annotation_text="Budget Ceiling",
                    annotation_position="right",
                    annotation_font=dict(color="#ff6b6b", size=11),
                )
                fig_burn.update_layout(
                    hoverlabel=_PLOT_HOVERLABEL,
                    legend=_PLOT_LEGEND,
                    font=dict(color="#e8f0f8", size=11),
                    title_font=dict(size=16, color="#e8f0f8"),
                    xaxis=dict(
                        tickfont=dict(color="#a0a9b8", size=10),
                        title_font=dict(color="#e8f0f8", size=12),
                        gridcolor="#2d3748",
                    ),
                    yaxis=dict(
                        tickfont=dict(color="#a0a9b8", size=10),
                        title_font=dict(color="#e8f0f8", size=12),
                        gridcolor="#2d3748",
                    ),
                    paper_bgcolor="#0E1117",
                    plot_bgcolor="#0E1117",
                )
                st.plotly_chart(fig_burn, use_container_width=True)
        else:
            st.info("No category data available for charts.")


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
        import tempfile
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
            import os
            os.unlink(tmp_path)
