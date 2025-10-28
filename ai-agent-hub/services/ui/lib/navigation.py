"""Navigation helpers for the modular Streamlit application."""
from __future__ import annotations

import streamlit as st


PAGES = {
    "Landing": "pages/1_Landing.py",
    "Login": "pages/2_Login.py",
    "CreditApp": "pages/3_CreditApp.py",
}


def set_active_page(page: str) -> None:
    st.session_state.active_page = page
    st.experimental_set_query_params(page=page)


def render_navbar() -> None:
    st.markdown(
        """
        <style>
        .nav-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #111827;
            padding: 0.5rem 1rem;
            border-radius: 8px;
        }
        .nav-title {
            color: #f9fafb;
            font-size: 1.2rem;
            font-weight: bold;
        }
        .nav-links a {
            color: #93c5fd;
            text-decoration: none;
            margin-left: 1rem;
            font-weight: 500;
        }
        </style>
        <div class="nav-container">
            <div class="nav-title">🧠 AI Sandbox by the People</div>
            <div class="nav-links">
                <a href="?page=Landing">🏠 Home</a>
                <a href="?page=CreditApp">💳 Credit</a>
                <a href="?page=Login">🔐 Login</a>
            </div>
        </div>
        <br>
        """,
        unsafe_allow_html=True,
    )
