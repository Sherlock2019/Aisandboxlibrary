 ────────────────────────────────
# STAGE: LOGIN
# ────────────────────────────────
if st.session_state.stage == "login":
    top = st.columns([1, 4, 1])
    with top[0]:
        if st.button("⬅️ Back to Agents", key="btn_back_agents_from_login"):
            st.session_state.stage = "agents"
            st.rerun()
    with top[1]:
        st.title("🔐 Login to AI Credit Appraisal Platform")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        user = st.text_input("Username", placeholder="e.g. dzoan")
    with c2:
        email = st.text_input("Email", placeholder="e.g. dzoan@demo.local")
    with c3:
        pwd = st.text_input("Password", type="password", placeholder="Enter any password")
    if st.button("Login", key="btn_login_submit", use_container_width=True):
        if user.strip() and email.strip():
            st.session_state.user_info = {
                "name": user.strip(),
                "email": email.strip(),
                "flagged": False,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            st.session_state.logged_in = True
            st.session_state.stage = "credit_agent"
            st.rerun()
        else:
            st.error("⚠️ Please fill all fields before continuing.")
    st.markdown("<footer>Made with ❤️ by Dzoan Nguyen — Open AI Sandbox Initiative</footer>", unsafe_allow_html=True)
    st.stop()
