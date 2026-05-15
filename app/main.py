import streamlit as st
import pandas as pd
import sys
import importlib
from datetime import date
from pathlib import Path
import plotly.express as px

# 1. Setup & Imports — project root from this file (not cwd) so reads/writes always hit the same CSVs
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(_PROJECT_ROOT))

from src.processor import clean_and_feature_engineer
from src import analytics as analytics_module
from src.insights import generate_automated_insights
from src.recommender import get_recommendations

analytics_module = importlib.reload(analytics_module)

st.set_page_config(page_title="Personal Finance Intelligence", layout="wide")

st.title("💰 Personal Finance Intelligence")
st.markdown("### Plan your goal, track daily spending, and get actionable recommendations.")
st.markdown(
    """
    <style>
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        /* Plotly hovers + legend: rounded SVG rects (not available via Python layout API). */
        div[data-testid="stPlotlyChart"] svg .hoverlayer g.hovertext > rect,
        div[data-testid="stPlotlyChart"] svg g.hovertext > rect,
        div[data-testid="stPlotlyChart"] svg .hovertext > rect {
            rx: 10px !important;
            ry: 10px !important;
        }
        div[data-testid="stPlotlyChart"] svg .infolayer .legend > rect.bg,
        div[data-testid="stPlotlyChart"] svg g.legend > rect.bg {
            rx: 10px !important;
            ry: 10px !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# 2. Data Engine — absolute paths + explicit reload contract (never trust a stale in-memory df after disk writes)
DATA_PATH = _PROJECT_ROOT / "data" / "raw" / "personal_expenses.csv"
PROCESSED_PATH = _PROJECT_ROOT / "data" / "processed" / "cleaned_expenses.csv"


def _parse_processed_dates(frame: pd.DataFrame) -> pd.DataFrame:
    if "date" in frame.columns:
        frame = frame.copy()
        frame["date"] = pd.to_datetime(frame["date"], dayfirst=True, errors="coerce")
    return frame


def rebuild_from_raw() -> pd.DataFrame:
    """Rebuild processed CSV from raw and return the parsed processed frame (single pipeline entry)."""
    clean_and_feature_engineer(str(DATA_PATH), str(PROCESSED_PATH))
    out = pd.read_csv(PROCESSED_PATH)
    return _parse_processed_dates(out)


# One authoritative load at startup (salary default, categories). Log tab uses this `df` until rerun.
df = rebuild_from_raw()
default_salary = float(df["income"].iloc[0]) if not df.empty and "income" in df.columns else 0.0
if "monthly_salary" not in st.session_state:
    st.session_state.monthly_salary = default_salary
if "savings_goal_pct" not in st.session_state:
    st.session_state.savings_goal_pct = 20.0
if "tracking_start_date" not in st.session_state:
    st.session_state.tracking_start_date = date.today()
# Canonical month for Recommendations (JSON-safe string "YYYY-MM"). Period objects in session_state are unreliable.
if "reco_period_str" not in st.session_state:
    st.session_state.reco_period_str = None  # None = "latest month with data"
RECO_MONTH_WIDGET_KEY = "reco_month_period_select"

# Plotly: elevated slate panels — clearly not the app chrome (#0E1117); white text reads cleanly.
# Rounded corners: see global <style> rules for .hovertext rect and .legend rect.bg (SVG).
_PLOT_PANEL_BG = "#3a4252"
_PLOT_PANEL_BORDER = "#8b95a8"
_PLOT_HOVERLABEL = dict(
    bgcolor=_PLOT_PANEL_BG,
    bordercolor=_PLOT_PANEL_BORDER,
    align="left",
    font=dict(color="#ffffff", size=14, family="Arial, sans-serif"),
)
_PLOT_LEGEND = dict(
    bgcolor=_PLOT_PANEL_BG,
    bordercolor=_PLOT_PANEL_BORDER,
    borderwidth=1,
    font=dict(color="#ffffff", size=12, family="Arial, sans-serif"),
    tracegroupgap=0,
)
# "Start tracking from" must live outside tabs so it runs every rerun (inactive tab bodies can be skipped).
# Also: this date must update session immediately — not only when "Save Goal Settings" is clicked.
st.sidebar.header("Tracking")
st.session_state.tracking_start_date = st.sidebar.date_input(
    "Start tracking from",
    value=st.session_state.tracking_start_date,
    help="Only expenses on or after this date count toward Spent in Recommendations.",
    key="sidebar_tracking_start",
)

tab_setup, tab_recommendations, tab_log = st.tabs(
    ["🎯 Goal Setup", "🤖 Recommendations", "📝 Daily Log"]
)

with tab_setup:
    st.subheader("Set Your Monthly Plan")
    salary_input = st.number_input(
        "Monthly Salary (INR)",
        min_value=0.0,
        value=float(st.session_state.monthly_salary),
        step=1000.0,
        key="salary_input"
    )
    goal_input = st.number_input(
        "Savings Goal (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(st.session_state.savings_goal_pct),
        step=1.0,
        key="goal_input"
    )

    if st.button("Save Goal Settings"):
        st.session_state.monthly_salary = salary_input
        st.session_state.savings_goal_pct = goal_input
        st.success("Salary and savings goal % saved. (Tracking date is set in the sidebar and applies immediately.)")

    planned_target = st.session_state.monthly_salary * (st.session_state.savings_goal_pct / 100)
    st.metric("Planned Monthly Savings Target", f"₹{planned_target:,.0f}")

with tab_log:
    st.subheader("Add Daily Expense")
    # Always show a full default list; merge with any categories already in your data (e.g. custom tags).
    _default_categories = [
        "Food",
        "Groceries",
        "Rent",
        "Bills",
        "Transport",
        "Shopping",
        "Travel",
        "Entertainment",
        "Health",
        "Education",
        "Subscriptions",
        "Misc",
    ]
    _from_data = (
        sorted(df["category"].dropna().astype(str).str.strip().unique().tolist())
        if "category" in df.columns
        else []
    )
    categories = sorted(set(_default_categories) | set(_from_data))

    with st.form("daily_log_form", clear_on_submit=True):
        txn_date = st.date_input("Date")
        txn_amount = st.number_input("Amount (INR)", min_value=0.0, step=100.0)
        txn_category = st.selectbox("Category", options=categories)
        txn_description = st.text_input("Description")
        submitted = st.form_submit_button("Add Transaction")

    if submitted and txn_amount > 0:
        raw_df = pd.read_csv(DATA_PATH)
        new_row = {
            "date": pd.Timestamp(txn_date).strftime("%d-%m-%Y"),
            "amount": float(txn_amount),
            "category": txn_category,
            "payment_mode": "UPI",
            "description": txn_description.strip() or "Manual Entry",
            "income": float(st.session_state.monthly_salary)
        }
        raw_df = pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True)
        raw_df.to_csv(DATA_PATH, index=False)
        # Root fix: in-memory `df` must match disk before the rest of this run (Recommendations runs after this block).
        df = rebuild_from_raw()
        # Jump Recommendations to the month you just logged (string — survives session serialization).
        st.session_state.reco_period_str = pd.Timestamp(txn_date).strftime("%Y-%m")
        # Streamlit persists selectbox state by key; `index=` is ignored once the widget exists — clear so new month wins.
        st.session_state.pop(RECO_MONTH_WIDGET_KEY, None)
        st.success("Transaction added successfully. Recommendations will refresh now.")
        st.rerun()

with tab_recommendations:
    st.subheader("Recommendations Based on Your Goal")
    # Always rebuild from raw here so Spent cannot lag behind Daily Log (OneDrive / partial writes / ordering).
    df = rebuild_from_raw()
    track_start = pd.Timestamp(st.session_state.tracking_start_date).normalize()
    dnorm = df["date"].dt.normalize()
    tracked_df = df[df["date"].notna() & (dnorm >= track_start)].copy()
    tracked_df["_period"] = tracked_df["date"].dt.to_period("M")
    periods = sorted(tracked_df["_period"].dropna().unique())
    # Widget options must be plain strings — Period objects in selectbox + session_state cause subtle mismatches.
    period_labels = [p.strftime("%Y-%m") for p in periods]

    if len(periods) == 0:
        selected_month_label = pd.Timestamp(st.session_state.tracking_start_date).strftime("%B %Y")
        monthly_df = tracked_df.iloc[0:0]
        selected_label = None
    else:
        raw_pref = st.session_state.reco_period_str
        if not raw_pref or raw_pref not in period_labels:
            raw_pref = period_labels[-1]
        idx = period_labels.index(raw_pref)

        def _fmt_period_label(label: str) -> str:
            return pd.Period(label, freq="M").strftime("%b %Y")

        selected_label = st.selectbox(
            "Select Month",
            options=period_labels,
            index=idx,
            format_func=_fmt_period_label,
            key=RECO_MONTH_WIDGET_KEY,
        )
        st.session_state.reco_period_str = selected_label
        selected_period = pd.Period(selected_label, freq="M")
        monthly_df = tracked_df[tracked_df["_period"] == selected_period]
        selected_month_label = selected_period.strftime("%B %Y")

    with st.expander("Why doesn’t Spent change? (data check)", expanded=False):
        st.code(
            f"RAW:  {DATA_PATH.resolve()}\nPROC: {PROCESSED_PATH.resolve()}",
            language="text",
        )
        raw_try = pd.read_csv(DATA_PATH)
        raw_try["date"] = pd.to_datetime(raw_try["date"], dayfirst=True, errors="coerce")
        max_d = df["date"].max()
        st.write(
            f"Raw rows: **{len(raw_try)}** · Processed rebuild rows: **{len(df)}** · "
            f"After start-tracking filter: **{len(tracked_df)}** (cutoff = **{st.session_state.tracking_start_date}**)"
        )
        if pd.notna(max_d):
            st.write(f"Latest expense date in processed data: **{max_d.date()}**")
        if len(raw_try) > 0:
            st.write(f"Latest raw `date` cell (string): **{raw_try['date'].iloc[-1]}**")
        if len(tracked_df) == 0 and len(df) > 0:
            st.warning(
                "No rows on/after your sidebar **Start tracking from** date — Spent stays 0. "
                "Move that date **earlier** (e.g. before your CSV’s first date) or add logs with dates **on/after** it."
            )
        if selected_label is not None and len(monthly_df) > 0:
            st.write(
                f"Month **{selected_label}**: direct sum(amount) = **₹{monthly_df['amount'].sum():,.0f}** "
                f"(same basis as Spent)."
            )

    try:
        summary = analytics_module.get_monthly_summary(
            monthly_df,
            monthly_income_override=st.session_state.monthly_salary,
            savings_goal_pct=st.session_state.savings_goal_pct
        )
    except TypeError:
        summary = analytics_module.get_monthly_summary(monthly_df)

    summary.setdefault(
        "target_savings",
        summary.get("total_income", 0) * (st.session_state.savings_goal_pct / 100)
    )
    summary.setdefault("savings_gap", summary.get("savings", 0) - summary.get("target_savings", 0))
    summary.setdefault(
        "savings_rate",
        (summary.get("savings", 0) / summary.get("total_income", 0) * 100) if summary.get("total_income", 0) > 0 else 0.0
    )
    if monthly_df.empty:
        summary["total_spent"] = 0.0
        summary["savings"] = 0.0
        summary["savings_rate"] = 0.0
        summary["category_shares"] = {}
        summary["growth"] = pd.DataFrame()
        summary["weekend_factor"] = {}
        summary["savings_gap"] = summary.get("savings", 0) - summary.get("target_savings", 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Income", f"₹{summary.get('total_income', 0):,.0f}")
    with col2:
        st.metric("Spent", f"₹{summary.get('total_spent', 0):,.0f}", delta_color="inverse")
    with col3:
        st.metric("Current Savings", f"₹{summary.get('savings', 0):,.0f}", delta=f"{summary.get('savings_rate', 0):.1f}%")
    with col4:
        st.metric("Target Savings INR", f"₹{summary.get('target_savings', 0):,.0f}", delta=f"₹{summary.get('savings_gap', 0):,.0f} vs Target")
    st.caption(
        f"Spent is for **{selected_month_label}** only ({len(monthly_df)} transactions on/after the sidebar **Start tracking from** date). "
        "Change **Select Month** if totals look unchanged after a new log."
    )

    st.markdown("#### How Much More To Save")
    if summary.get("savings_gap", 0) >= 0:
        st.success(f"You are ahead of target by ₹{summary.get('savings_gap', 0):,.0f}.")
    else:
        st.error(f"You need to save ₹{abs(summary.get('savings_gap', 0)):,.0f} more to hit your goal this month.")

    col_coach_1, col_coach_2 = st.columns(2)
    with col_coach_1:
        st.markdown("#### 💡 Insights")
        for insight in generate_automated_insights(summary):
            st.write(insight)
    with col_coach_2:
        st.markdown("#### 🎯 Recommendations")
        for rec in get_recommendations(summary):
            st.write(rec)

    st.divider()
    st.markdown("#### Spending Deep Dive")
    if monthly_df.empty:
        st.info("No tracked transactions yet for this period. Add entries in Daily Log to build your charts.")
    else:
        category_data = summary.get("category_shares", {})

        fig_pie = px.pie(
            names=list(category_data.keys()),
            values=list(category_data.values()),
            hole=0.4,
            title=f"Spending Distribution: {selected_month_label}",
            template="plotly_dark"
        )
        fig_pie.update_layout(
            hoverlabel=_PLOT_HOVERLABEL,
            legend=_PLOT_LEGEND,
        )
        st.plotly_chart(fig_pie, width="stretch")

        burn_df = monthly_df.sort_values("date")
        fig_burn = px.line(
            burn_df,
            x="date",
            y="cumulative_spent",
            title=f"Cumulative Spending Trend: {selected_month_label}",
            labels={"cumulative_spent": "Total Spent (INR)", "date": "Date"},
            template="plotly_dark"
        )
        fig_burn.add_hline(
            y=summary.get("total_income", 0),
            line_dash="dash",
            line_color="red",
            annotation_text="Budget Ceiling"
        )
        fig_burn.update_layout(
            hoverlabel=_PLOT_HOVERLABEL,
            legend=_PLOT_LEGEND,
            xaxis=dict(tickfont=dict(color="white")),
            yaxis=dict(tickfont=dict(color="white")),
        )
        st.plotly_chart(fig_burn, width="stretch")