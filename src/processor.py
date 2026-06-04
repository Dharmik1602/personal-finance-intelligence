"""
processor.py — Data cleaning and feature engineering.

UPGRADE: Now accepts a DataFrame directly (from the DB) instead of
reading a CSV file. The function signature is backward-compatible:
if you pass a file path string it still works, but the DB-backed
main.py passes a DataFrame.
"""

import pandas as pd
from pathlib import Path


def clean_and_feature_engineer(data: pd.DataFrame | str) -> pd.DataFrame:
    """
    Accept either:
      - a pandas DataFrame (from the DB), or
      - a file path string / Path (legacy CSV mode)

    Returns a cleaned, feature-engineered DataFrame ready for analytics.
    """
    # ── Load ──────────────────────────────────────────────────────────────────
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data, parse_dates=["date"])
    else:
        df = data.copy()

    if df.empty:
        return df

    # ── Normalise column names ────────────────────────────────────────────────
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # ── Parse dates ───────────────────────────────────────────────────────────
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], infer_datetime_format=True, errors="coerce")

    df.dropna(subset=["date", "amount"], inplace=True)

    # ── Coerce numerics ───────────────────────────────────────────────────────
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0).abs()

    if "income" in df.columns:
        df["income"] = pd.to_numeric(df["income"], errors="coerce").fillna(0)
    else:
        df["income"] = 0

    # ── Fill optional cols ────────────────────────────────────────────────────
    df["category"]     = df.get("category",     pd.Series("Other",    index=df.index)).fillna("Other")
    df["description"]  = df.get("description",  pd.Series("",         index=df.index)).fillna("")
    df["payment_mode"] = df.get("payment_mode", pd.Series("Unknown",  index=df.index)).fillna("Unknown")

    # ── Feature engineering ───────────────────────────────────────────────────
    df["month"]        = df["date"].dt.to_period("M")
    df["month_name"]   = df["date"].dt.strftime("%B %Y")
    df["day_of_week"]  = df["date"].dt.day_name()
    df["is_weekend"]   = df["date"].dt.dayofweek >= 5

    # Cumulative spend within each month (burn rate)
    df.sort_values("date", inplace=True)
    df["cumulative_spent"] = df.groupby("month")["amount"].cumsum()

    df.reset_index(drop=True, inplace=True)
    return df
