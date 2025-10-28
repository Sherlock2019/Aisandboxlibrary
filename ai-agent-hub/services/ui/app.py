import streamlit as st

st.set_page_config(
    page_title="AI Agent Sandbox",
    page_icon="🧠",
    layout="wide"
)

# --- Session Setup ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "active_page" not in st.session_state:
    st.session_state.active_page = "Landing"

# --- Top Navbar ---
def show_navbar():
    st.markdown("""
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
                <a href="?page=AssetApp">🏛️ Asset</a>
                <a href="?page=Logout">🚪 Logout</a>
            </div>
        </div>
        <br>
    """, unsafe_allow_html=True)

# --- Routing ---
query_params = st.query_params
page = query_params.get("page", [st.session_state.active_page])[0]

if not st.session_state.logged_in and page not in ["Login"]:
    st.switch_page("pages/1_Login.py")
else:
    show_navbar()
    if page == "Landing":
        st.switch_page("pages/2_Landing.py")
    elif page == "CreditApp":
        st.switch_page("pages/3_CreditApp.py")
    elif page == "AssetApp":
        st.switch_page("pages/4_AssetApp.py")
    elif page == "Logout":
        st.session_state.logged_in = False
        st.switch_page("pages/1_Login.py")
