"""
auth_page.py — Login / Register Streamlit page.
Call render_auth_page() before the main dashboard.
It writes user info into st.session_state on success.
"""

import streamlit as st
from src.auth import register_user, login_user


def render_auth_page():
    """
    Renders login/register UI. Sets st.session_state['user'] on success.
    Returns True once authenticated, False otherwise.
    """
    # Already authenticated — skip
    if st.session_state.get("user"):
        return True

    st.markdown(
        """
        <style>
        /* Centre the auth card */
        [data-testid="stAppViewContainer"] > .main {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .auth-card {
            background: #1e1e2e;
            border-radius: 16px;
            padding: 2.5rem 2rem;
            max-width: 420px;
            margin: auto;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        .auth-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #cdd6f4;
            margin-bottom: 0.2rem;
        }
        .auth-sub {
            color: #6c7086;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## 💰 Personal Finance Intelligence")
    st.markdown("Track. Analyse. Save smarter.")
    st.divider()

    tab_login, tab_register = st.tabs(["🔑 Login", "✨ Create Account"])

    # ── LOGIN ─────────────────────────────────────────────────────────────────
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please fill in all fields.")
            else:
                ok, msg, user = login_user(username, password)
                if ok:
                    st.session_state["user"] = user
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # ── REGISTER ──────────────────────────────────────────────────────────────
    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("Username", key="reg_user")
            new_email    = st.text_input("Email",    key="reg_email")
            new_pass     = st.text_input("Password", type="password", key="reg_pass")
            new_pass2    = st.text_input("Confirm Password", type="password", key="reg_pass2")
            submitted_r  = st.form_submit_button("Create Account", use_container_width=True)

        if submitted_r:
            if not all([new_username, new_email, new_pass, new_pass2]):
                st.error("Please fill in all fields.")
            elif new_pass != new_pass2:
                st.error("Passwords do not match.")
            else:
                ok, msg = register_user(new_username, new_email, new_pass)
                if ok:
                    st.success(msg + " Switch to the Login tab.")
                else:
                    st.error(msg)

    return False  # Not yet authenticated
