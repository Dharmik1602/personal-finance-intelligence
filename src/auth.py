"""
auth.py — Registration and login helpers for Personal Finance Intelligence.
Passwords are hashed with bcrypt; never stored in plain text.
"""

import bcrypt
from src.database import create_user, get_user_by_username, get_user_by_email


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Auth actions ──────────────────────────────────────────────────────────────

def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """
    Validate and create a new user.
    Returns (success: bool, message: str).
    """
    username = username.strip()
    email = email.strip().lower()

    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if "@" not in email:
        return False, "Enter a valid email address."
    if get_user_by_username(username):
        return False, "Username already taken."
    if get_user_by_email(email):
        return False, "An account with that email already exists."

    hashed = hash_password(password)
    create_user(username, email, hashed)
    return True, "Account created! You can now log in."


def login_user(username: str, password: str) -> tuple[bool, str, dict | None]:
    """
    Verify credentials.
    Returns (success, message, user_dict | None).
    """
    user = get_user_by_username(username.strip())
    if not user:
        return False, "Username not found.", None
    if not check_password(password, user["password"]):
        return False, "Incorrect password.", None
    return True, f"Welcome back, {user['username']}!", user
