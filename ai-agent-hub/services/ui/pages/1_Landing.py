from __future__ import annotations

import streamlit as st

from lib import (
    PAGES,
    apply_form_styles,
    ensure_session_defaults,
    render_agent_catalog,
    save_uploaded_image,
    load_image,
    set_active_page,
    show_footer,
)

ensure_session_defaults()
apply_form_styles()
set_active_page("Landing")

c1, c2 = st.columns([1.1, 1.9], gap="large")
with c1:
    st.markdown("<div class='left-box'>", unsafe_allow_html=True)
    logo_path = load_image("people_logo")
    if logo_path:
        st.image(logo_path, width=160)
    else:
        uploaded_logo = st.file_uploader("Upload People Logo", type=["jpg", "png", "webp"], key="upload_logo")
        if uploaded_logo:
            save_uploaded_image(uploaded_logo, "people_logo")
            st.success("✅ Logo uploaded, refresh to view.")
    st.markdown(
        """
        <h1>✊ Let’s Build an AI by the People, for the People</h1>
        <h3>⚙️ Ready-to-Use AI Agent Sandbox — From Sandbox to Production</h3>
        <p>Build, test, and deploy AI agents using open-source explainable models.<br><br>
        <b>Privacy:</b> Synthetic & anonymized data only.<br>
        <b>Deployment:</b> GPU-as-a-Service Cloud, zero CAPEX.</p>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🚀 Start Building Now", key="btn_start_build_now"):
        set_active_page("Login")
        st.switch_page(PAGES["Login"])
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='right-box'>", unsafe_allow_html=True)
    st.markdown("<h2>📊 Global AI Agent Library</h2>", unsafe_allow_html=True)
    render_agent_catalog()
    st.markdown("</div>", unsafe_allow_html=True)

show_footer()
