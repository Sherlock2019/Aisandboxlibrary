from __future__ import annotations

import datetime as dt

import streamlit as st

from lib import PAGES, apply_form_styles, ensure_session_defaults, set_active_page, show_footer

ensure_session_defaults()
apply_form_styles()
set_active_page("Login")

cols = st.columns([1, 4, 1])
with cols[0]:
    if st.button("⬅️ Back to Home", key="btn_back_home_from_login"):
        set_active_page("Landing")
        st.switch_page(PAGES["Landing"])
with cols[1]:
    st.title("🔐 Login to AI Credit Appraisal Platform")

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    username = st.text_input("Username", placeholder="e.g. dzoan")
with c2:
    email = st.text_input("Email", placeholder="e.g. dzoan@demo.local")
with c3:
    password = st.text_input("Password", type="password", placeholder="Enter any password")

if st.button("Login", key="btn_login_submit", use_container_width=True):
    if username.strip() and email.strip():
        st.session_state.user_info = {
            "name": username.strip(),
            "email": email.strip(),
            "flagged": False,
            "timestamp": dt.datetime.utcnow().isoformat(),
        }
        st.session_state.logged_in = True
        set_active_page("CreditApp")
        st.switch_page(PAGES["CreditApp"])
    else:
        st.error("⚠️ Please fill all fields before continuing.")

show_footer()
