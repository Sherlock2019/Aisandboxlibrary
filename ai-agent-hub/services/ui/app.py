from __future__ import annotations

import streamlit as st

from lib import (
    PAGES,
    apply_global_styles,
    ensure_session_defaults,
    render_navbar,
)

st.set_page_config(
    page_title="AI Agent Sandbox",
    page_icon="🧠",
    layout="wide",
)

ensure_session_defaults()
apply_global_styles()

query_params = st.query_params
requested_page = query_params.get("page", [st.session_state.active_page])[0]
if requested_page not in PAGES:
    requested_page = "Landing"
st.session_state.active_page = requested_page

if not st.session_state.logged_in and requested_page not in {"Landing", "Login"}:
    st.switch_page(PAGES["Login"])
else:
    render_navbar()
    st.switch_page(PAGES[requested_page])
