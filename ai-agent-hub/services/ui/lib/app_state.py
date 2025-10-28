"""Application-level configuration and Streamlit helpers."""
from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path
from typing import Optional

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
LANDING_IMG_DIR = BASE_DIR / "landing_images"
RUNS_DIR = BASE_DIR / ".runs"
TMP_FEEDBACK_DIR = BASE_DIR / ".tmp_feedback"

for directory in (LANDING_IMG_DIR, RUNS_DIR, TMP_FEEDBACK_DIR):
    directory.mkdir(parents=True, exist_ok=True)

API_URL = os.getenv("API_URL", "http://localhost:8090")


_GLOBAL_STYLE = """
<style>
body, .stApp {
    background-color: #0f172a !important;
    color: #e5e7eb !important;
    font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"], .stApp header {
    background: #0f172a !important;
    color: #f8fafc !important;
    border-bottom: 1px solid #1e293b !important;
}
h1, h2, h3 {
    color: #f8fafc !important;
    font-weight: 800 !important;
    text-shadow: 0 0 8px rgba(37,99,235,0.6),
                 0 0 16px rgba(59,130,246,0.3);
}
.stSubheader, h4, h5, h6 {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
    text-shadow: 0 0 4px rgba(37,99,235,0.4);
}
div[data-baseweb="tab"] > button {
    color: #cbd5e1 !important;
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
div[data-baseweb="tab"] > button[aria-selected="true"] {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white !important;
    border: none !important;
    box-shadow: 0 0 12px rgba(37,99,235,0.5);
    transform: scale(1.05);
}
.stExpander, .stFileUploader, .stDataFrame, .stJson, .stMetric {
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
    border-radius: 10px !important;
}
[data-testid="stDataFrame"] thead tr th {
    color: #f1f5f9 !important;
    background-color: #1e293b !important;
    border-bottom: 1px solid #334155 !important;
}
[data-testid="stDataFrame"] tbody tr td {
    color: #e2e8f0 !important;
}
input, select, textarea {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}
.stButton > button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    padding: 10px 26px !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3),
                0 0 10px rgba(37,99,235,0.4);
    transition: all 0.25s ease-in-out;
}
.stButton > button:hover {
    transform: translateY(-3px);
    background: linear-gradient(90deg, #1e40af, #1e3a8a) !important;
    box-shadow: 0 6px 18px rgba(0,0,0,0.4),
                0 0 18px rgba(37,99,235,0.6);
}
a {
    color: #60a5fa !important;
    text-decoration: none !important;
}
a:hover {
    color: #93c5fd !important;
    text-shadow: 0 0 6px rgba(96,165,250,0.6);
}
.stFileUploader {
    border: 1px solid #334155 !important;
    background-color: #1e293b !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    box-shadow: inset 0 0 8px rgba(37,99,235,0.25);
}
::-webkit-scrollbar {
    width: 10px;
}
::-webkit-scrollbar-track {
    background: #1e293b;
}
::-webkit-scrollbar-thumb {
    background: #3b82f6;
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: #60a5fa;
}
html, body, .block-container {
    background-color:#0f172a !important;
    color:#e2e8f0 !important;
}
footer {
    text-align:center;
    padding:2rem;
    color:#aab3c2;
    font-size:1.2rem;
    font-weight:600;
    margin-top:2rem;
}
.left-box {
    background: radial-gradient(circle at top left, #0f172a, #1e293b);
    border-radius:20px;
    padding:3rem 2rem;
    color:#f1f5f9;
    box-shadow:6px 0 24px rgba(0,0,0,0.4);
}
.right-box {
    background:linear-gradient(180deg,#1e293b,#0f172a);
    border-radius:20px;
    padding:2rem;
    box-shadow:-6px 0 24px rgba(0,0,0,0.35);
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-size: 28px !important;
    font-weight: 800 !important;
    padding: 20px 40px !important;
    border-radius: 12px !important;
    background-color: #1e293b !important;
    color: #f8fafc !important;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border-bottom: 6px solid #60a5fa !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.5);
}
</style>
"""

_FORM_STYLE = """
<style>
input, select, textarea, .stTextInput, .stSelectbox, .stNumberInput {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: 1px solid #3b82f6 !important;
    border-radius: 8px !important;
    font-size: 18px !important;
    font-weight: 600 !important;
    padding: 8px 12px !important;
}
div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    font-size: 18px !important;
}
ul[role="listbox"] li {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    font-size: 18px !important;
}
ul[role="listbox"] li:hover {
    background-color: #2563eb !important;
    color: white !important;
}
[data-baseweb="slider"] div[role="slider"] {
    background-color: #3b82f6 !important;
}
[data-baseweb="slider"] div {
    height: 8px !important;
}
[data-testid="stSliderTickBar"] {
    background-color: #334155 !important;
}
label, .stMarkdown p, .stCaption, .stText {
    font-size: 18px !important;
    color: #f1f5f9 !important;
    font-weight: 500 !important;
}
h2, h3, h4, .stSubheader {
    font-size: 26px !important;
    color: #f8fafc !important;
    text-shadow: 0 0 8px rgba(59,130,246,0.4);
}
[data-testid="stExpander"] > div:first-child {
    background-color: #111827 !important;
    color: #f8fafc !important;
    font-size: 20px !important;
    font-weight: 700 !important;
}
div[data-baseweb="tab"] > button {
    font-size: 18px !important;
    padding: 10px 18px !important;
}
.stMarkdown, .stText, p, span, div {
    font-size: 18px !important;
}
div[role="radio"], div[role="checkbox"] label, label[data-baseweb="radio"], label[data-baseweb="checkbox"] {
    color: #f8fafc !important;
    font-size: 18px !important;
    font-weight: 600 !important;
}
div[role="radio"] p, div[role="checkbox"] p {
    color: #e2e8f0 !important;
    font-size: 16px !important;
}
.stRadio label {
    color: #f1f5f9 !important;
    font-weight: 600 !important;
}
[data-testid="stCheckbox"] label {
    color: #f8fafc !important;
    font-size: 18px !important;
    font-weight: 700 !important;
}
</style>
"""

_DOWNLOAD_BUTTON_STYLE = """
<style>
div[data-testid="stDownloadButton"] button {
    font-size: 90px !important;
    font-weight: 900 !important;
    padding: 28px 48px !important;
    border-radius: 16px !important;
    background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 6px 18px rgba(0,0,0,0.35) !important;
    transition: all 0.3s ease-in-out !important;
}
div[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(90deg, #1e3a8a, #1d4ed8) !important;
    transform: scale(1.03);
}
</style>
"""


def ensure_session_defaults() -> None:
    """Populate default session state values used across pages."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = {
            "name": "",
            "email": "",
            "flagged": False,
            "timestamp": _dt.datetime.utcnow().isoformat(),
        }
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Landing"

    from .credit import ensure_currency_defaults  # local import to avoid circular

    ensure_currency_defaults()


def apply_global_styles() -> None:
    """Inject the shared CSS used across the application."""
    st.markdown(_GLOBAL_STYLE, unsafe_allow_html=True)


def apply_form_styles(include_download: bool = False) -> None:
    """Inject styling for forms and optionally the large download button."""
    st.markdown(_FORM_STYLE, unsafe_allow_html=True)
    if include_download:
        st.markdown(_DOWNLOAD_BUTTON_STYLE, unsafe_allow_html=True)


def load_image(base: str) -> Optional[str]:
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"):
        path = LANDING_IMG_DIR / f"{base}{ext}"
        if path.exists():
            return str(path)
    return None


def save_uploaded_image(uploaded_file, base: str) -> Optional[str]:
    if not uploaded_file:
        return None
    ext = Path(uploaded_file.name).suffix or ".png"
    dest = LANDING_IMG_DIR / f"{base}{ext.lower()}"
    dest.write_bytes(uploaded_file.getvalue())
    return str(dest)


def render_image_tag(agent_id: str, industry: str, emoji_fallback: str) -> str:
    base = agent_id.lower().replace(" ", "_")
    img_path = load_image(base) or load_image(industry.replace(" ", "_"))
    if img_path:
        return (
            f'<img src="file://{img_path}" '
            "style=\"width:48px;height:48px;border-radius:10px;object-fit:cover;\">"
        )
    return f'<div style="font-size:32px;">{emoji_fallback}</div>'


def show_footer() -> None:
    st.markdown(
        "<footer>Made with ❤️ by Dzoan Nguyen — Open AI Sandbox Initiative</footer>",
        unsafe_allow_html=True,
    )
