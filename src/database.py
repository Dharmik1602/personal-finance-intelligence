"""
database.py — SQLite layer for Personal Finance Intelligence
All DB setup, user management, and transaction CRUD lives here.
"""

import sqlite3
import os
import pandas as pd
from pathlib import Path

# DB file lives next to the project root
DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"


def get_connection() -> sqlite3.Connection:
    """Return a connection with row_factory set for dict-like access."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist. Safe to call on every startup."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,          -- bcrypt hash
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id),
            date         TEXT    NOT NULL,          -- ISO 8601 YYYY-MM-DD
            amount       REAL    NOT NULL,
            category     TEXT    NOT NULL,
            description  TEXT,
            payment_mode TEXT,
            income       REAL    DEFAULT 0,         -- monthly salary snapshot
            created_at   TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS user_goals (
            user_id         INTEGER PRIMARY KEY REFERENCES users(id),
            monthly_salary  REAL    DEFAULT 0,
            savings_pct     REAL    DEFAULT 20       -- target savings %
        );

        CREATE INDEX IF NOT EXISTS idx_tx_user_date
            ON transactions(user_id, date);
    """)

    conn.commit()
    conn.close()


# ── User helpers ─────────────────────────────────────────────────────────────

def create_user(username: str, email: str, hashed_pw: str) -> int:
    """Insert a new user. Returns new user id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username.strip().lower(), email.strip().lower(), hashed_pw),
    )
    conn.commit()
    user_id = cur.lastrowid
    # Initialise goals row
    cur.execute(
        "INSERT OR IGNORE INTO user_goals (user_id) VALUES (?)", (user_id,)
    )
    conn.commit()
    conn.close()
    return user_id


def get_user_by_username(username: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username.strip().lower(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Goal helpers ──────────────────────────────────────────────────────────────

def get_goals(user_id: int) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT monthly_salary, savings_pct FROM user_goals WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else {"monthly_salary": 0, "savings_pct": 20}


def save_goals(user_id: int, monthly_salary: float, savings_pct: float):
    conn = get_connection()
    conn.execute(
        """INSERT INTO user_goals (user_id, monthly_salary, savings_pct)
           VALUES (?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET
               monthly_salary = excluded.monthly_salary,
               savings_pct    = excluded.savings_pct""",
        (user_id, monthly_salary, savings_pct),
    )
    conn.commit()
    conn.close()


# ── Transaction helpers ───────────────────────────────────────────────────────

def add_transaction(
    user_id: int,
    date: str,
    amount: float,
    category: str,
    description: str = "",
    payment_mode: str = "",
    income: float = 0,
):
    conn = get_connection()
    conn.execute(
        """INSERT INTO transactions
               (user_id, date, amount, category, description, payment_mode, income)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, date, amount, category, description, payment_mode, income),
    )
    conn.commit()
    conn.close()


def get_transactions_df(user_id: int) -> pd.DataFrame:
    """Return all transactions for a user as a pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT date, amount, category, description, payment_mode, income "
        "FROM transactions WHERE user_id = ? ORDER BY date",
        conn,
        params=(user_id,),
    )
    conn.close()
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def import_csv_for_user(user_id: int, csv_path: str):
    """
    Bulk-import an existing CSV into the DB for a user.
    Expects columns: date, amount, category, and optionally
    description, payment_mode, income.
    """
    df = pd.read_csv(csv_path, parse_dates=["date"])
    conn = get_connection()
    for _, row in df.iterrows():
        conn.execute(
            """INSERT INTO transactions
                   (user_id, date, amount, category, description, payment_mode, income)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                str(row["date"].date()),
                float(row.get("amount", 0)),
                str(row.get("category", "Other")),
                str(row.get("description", "")),
                str(row.get("payment_mode", "")),
                float(row.get("income", 0)),
            ),
        )
    conn.commit()
    conn.close()
