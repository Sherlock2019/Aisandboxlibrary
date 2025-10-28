# services/ui/app.py
# ─────────────────────────────────────────────
# 🌐 OpenSource AI Agent Library + Credit Appraisal PoC by Dzoan
# ─────────────────────────────────────────────
from __future__ import annotations
import os
import re
import io
import json
import datetime
from typing import Optional, Dict, List, Any

import pandas as pd
import numpy as np
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go


# ────────────────────────────────
# 🔁 Manage active tab navigation manually
# ────────────────────────────────
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "tab_gen"  # or whichever tab should open by default

def switch_tab(tab_name: str):
    """Programmatically switch between workflow tabs."""
    st.session_state.active_tab = tab_name
    st.rerun()


# ─────────────────────────────────────────────
# 🌌 GLOBAL DARK THEME + BLUE GLOW ENHANCED UI
st.markdown("""
<style>
/* ─────────────────────────────
   GLOBAL BACKGROUND + TEXT
───────────────────────────── */
body, .stApp {
    background-color: #0f172a !important;   /* very dark navy */
    color: #e5e7eb !important;
    font-family: 'Inter', sans-serif;
}

/* ─────────────────────────────
   HEADER + TITLE AREA
───────────────────────────── */
[data-testid="stHeader"], .stApp header {
    background: #0f172a !important;
    color: #f8fafc !important;
    border-bottom: 1px solid #1e293b !important;
}

/* Main App Title — add neon blue glow */
h1, h2, h3 {
    color: #f8fafc !important;
    font-weight: 800 !important;
    text-shadow: 0 0 8px rgba(37,99,235,0.6),
                 0 0 16px rgba(59,130,246,0.3);
}

/* Subheaders (like Human Review, Credit Appraisal, etc.) */
.stSubheader, h4, h5, h6 {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
    text-shadow: 0 0 4px rgba(37,99,235,0.4);
}

/* ─────────────────────────────
   TAB BAR
───────────────────────────── */
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

/* ─────────────────────────────
   BOXES, EXPANDERS, AND CONTAINERS
───────────────────────────── */
.stExpander, .stFileUploader, .stDataFrame, .stJson, .stMetric {
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
    border-radius: 10px !important;
}

/* DataFrames */
[data-testid="stDataFrame"] thead tr th {
    color: #f1f5f9 !important;
    background-color: #1e293b !important;
    border-bottom: 1px solid #334155 !important;
}
[data-testid="stDataFrame"] tbody tr td {
    color: #e2e8f0 !important;
}

/* Inputs & Selectors */
input, select, textarea {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}

/* ─────────────────────────────
   BUTTONS
───────────────────────────── */
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

/* ─────────────────────────────
   LINK STYLES
───────────────────────────── */
a {
    color: #60a5fa !important;
    text-decoration: none !important;
}
a:hover {
    color: #93c5fd !important;
    text-shadow: 0 0 6px rgba(96,165,250,0.6);
}

/* ─────────────────────────────
   FILE UPLOADER + PROGRESS
───────────────────────────── */
.stFileUploader {
    border: 1px solid #334155 !important;
    background-color: #1e293b !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    box-shadow: inset 0 0 8px rgba(37,99,235,0.25);
}

/* ─────────────────────────────
   SCROLLBARS (for aesthetics)
───────────────────────────── */
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
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 🌟 READABILITY & INPUT FIELD FIX PATCH

st.markdown("""
<style>
/* ─────────────────────────────
   FIX: Input Fields + Dropdowns Too Dark
───────────────────────────── */
input, select, textarea, .stTextInput, .stSelectbox, .stNumberInput {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: 1px solid #3b82f6 !important;
    border-radius: 8px !important;
    font-size: 18px !important;
    font-weight: 600 !important;
    padding: 8px 12px !important;
}

/* Dropdown menu items */
div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    font-size: 18px !important;
}

/* Dropdown list options */
ul[role="listbox"] li {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    font-size: 18px !important;
}
ul[role="listbox"] li:hover {
    background-color: #2563eb !important;
    color: white !important;
}

/* Sliders — brighter and thicker */
[data-baseweb="slider"] div[role="slider"] {
    background-color: #3b82f6 !important;
}
[data-baseweb="slider"] div {
    height: 8px !important;
}
[data-testid="stSliderTickBar"] {
    background-color: #334155 !important;
}

/* Labels + Captions */
label, .stMarkdown p, .stCaption, .stText {
    font-size: 18px !important;
    color: #f1f5f9 !important;
    font-weight: 500 !important;
}

/* Subheaders and Section Titles */
h2, h3, h4, .stSubheader {
    font-size: 26px !important;
    color: #f8fafc !important;
    text-shadow: 0 0 8px rgba(59,130,246,0.4);
}

/* Decision Rule Section Styling */
[data-testid="stExpander"] > div:first-child {
    background-color: #111827 !important;
    color: #f8fafc !important;
    font-size: 20px !important;
    font-weight: 700 !important;
}

/* Tabs — make them more visible and larger text */
div[data-baseweb="tab"] > button {
    font-size: 18px !important;
    padding: 10px 18px !important;
}

/* Global font size bump */
.stMarkdown, .stText, p, span, div {
    font-size: 18px !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* Brighten all radio + checkbox labels */
div[role="radio"], div[role="checkbox"] label, label[data-baseweb="radio"], label[data-baseweb="checkbox"] {
    color: #f8fafc !important;
    font-size: 18px !important;
    font-weight: 600 !important;
}

/* Fix small sub-labels near checkboxes */
div[role="radio"] p, div[role="checkbox"] p {
    color: #e2e8f0 !important;
    font-size: 16px !important;
}

/* Make rule mode label visible */
.stRadio label {
    color: #f1f5f9 !important;
    font-weight: 600 !important;
}

/* "Use LLM narrative" checkbox label */
[data-testid="stCheckbox"] label {
    color: #f8fafc !important;
    font-size: 18px !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 🔁 Manage active tab navigation manually (INSERT HERE)
# ─────────────────────────────────────────────
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "tab_gen"  # or tab_train if you want to start from training

def switch_tab(tab_name: str):
    """Programmatically switch between workflow tabs."""
    st.session_state.active_tab = tab_name
    st.rerun()


# ────────────────────────────────
# GLOBAL CONFIG
# ────────────────────────────────
BASE_DIR = os.path.expanduser("~/credit-appraisal-agent-poc/services/ui")
LANDING_IMG_DIR = os.path.join(BASE_DIR, "landing_images")
RUNS_DIR = os.path.join(BASE_DIR, ".runs")
TMP_FEEDBACK_DIR = os.path.join(BASE_DIR, ".tmp_feedback")

for d in (LANDING_IMG_DIR, RUNS_DIR, TMP_FEEDBACK_DIR):
    os.makedirs(d, exist_ok=True)

API_URL = os.getenv("API_URL", "http://localhost:8090")

# ────────────────────────────────
# SESSION STATE INIT
# ────────────────────────────────
if "stage" not in st.session_state:
    st.session_state.stage = "landing"
if "user_info" not in st.session_state:
    st.session_state.user_info = {"name": "", "email": "", "flagged": False}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "flagged" not in st.session_state.user_info:
    st.session_state.user_info["flagged"] = False
if "timestamp" not in st.session_state.user_info:
    st.session_state.user_info["timestamp"] = datetime.datetime.utcnow().isoformat()

# ────────────────────────────────
# PAGE CONFIG
# ────────────────────────────────
st.set_page_config(
    page_title="AI Agent Sandbox — By the People, For the People",
    layout="wide",
)

# ────────────────────────────────
# HELPERS
# ────────────────────────────────
def _clear_qp():
    """Clear query params (modern Streamlit API)."""
    try:
        st.query_params.clear()
    except Exception:
        pass


def load_image(base: str) -> Optional[str]:
    for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]:
        p = os.path.join(LANDING_IMG_DIR, f"{base}{ext}")
        if os.path.exists(p):
            return p
    return None


def save_uploaded_image(uploaded_file, base: str):
    if not uploaded_file:
        return None
    ext = os.path.splitext(uploaded_file.name)[1].lower() or ".png"
    dest = os.path.join(LANDING_IMG_DIR, f"{base}{ext}")
    with open(dest, "wb") as f:
        f.write(uploaded_file.getvalue())
    return dest


def render_image_tag(agent_id: str, industry: str, emoji_fallback: str) -> str:
    base = agent_id.lower().replace(" ", "_")
    img_path = load_image(base) or load_image(industry.replace(" ", "_"))
    if img_path:
        return (
            f'<img src="file://{img_path}" '
            f'style="width:48px;height:48px;border-radius:10px;object-fit:cover;">'
        )
    return f'<div style="font-size:32px;">{emoji_fallback}</div>'


# # ────────────────────────────────
# # DATA
# # ────────────────────────────────
# AGENTS = [
#     ("🏦 Banking & Finance", "💰 Retail Banking", "💳 Credit Appraisal Agent",
#      "Explainable AI for loan decisioning", "Available", "💳"),
#     ("🏦 Banking & Finance", "💰 Retail Banking", "🏦 Asset Appraisal Agent",
#      "Market-driven collateral valuation", "Coming Soon", "🏦"),
#     ("🏦 Banking & Finance", "🩺 Insurance", "🩺 Claims Triage Agent",
#      "Automated claims prioritization", "Coming Soon", "🩺"),
#     ("⚡ Energy & Sustainability", "🔋 EV & Charging", "⚡ EV Charger Optimizer",
#      "Optimize charger deployment via AI", "Coming Soon", "⚡"),
#     ("⚡ Energy & Sustainability", "☀️ Solar", "☀️ Solar Yield Estimator",
#      "Estimate solar ROI and efficiency", "Coming Soon", "☀️"),
#     ("🚗 Automobile & Transport", "🚙 Automobile", "🚗 Predictive Maintenance",
#      "Prevent downtime via sensor analytics", "Coming Soon", "🚗"),
#     ("🚗 Automobile & Transport", "🔋 EV", "🔋 EV Battery Health Agent",
#      "Monitor EV battery health cycles", "Coming Soon", "🔋"),
#     ("🚗 Automobile & Transport", "🚚 Ride-hailing / Logistics", "🛻 Fleet Route Optimizer",
#      "Dynamic route optimization for fleets", "Coming Soon", "🛻"),
#     ("💻 Information Technology", "🧰 Support & Security", "🧩 IT Ticket Triage",
#      "Auto-prioritize support tickets", "Coming Soon", "🧩"),
#     ("💻 Information Technology", "🛡️ Security", "🔐 SecOps Log Triage",
#      "Detect anomalies & summarize alerts", "Coming Soon", "🔐"),
#     ("⚖️ Legal & Government", "⚖️ Law Firms", "⚖️ Contract Analyzer",
#      "Extract clauses and compliance risks", "Coming Soon", "⚖️"),
#     ("⚖️ Legal & Government", "🏛️ Public Services", "🏛️ Citizen Service Agent",
#      "Smart assistant for citizen services", "Coming Soon", "🏛️"),
#     ("🛍️ Retail / SMB / Creative", "🏬 Retail & eCommerce", "📈 Sales Forecast Agent",
#      "Predict demand & inventory trends", "Coming Soon", "📈"),
#     ("🎬 Retail / SMB / Creative", "🎨 Media & Film", "🎬 Budget Cost Assistant",
#      "Estimate, optimize, and track film & production costs using AI", "Coming Soon", "🎬"),
# ]

# ────────────────────────────────
# STYLES
# ────────────────────────────────
st.markdown(
    """
    <style>
    html, body, .block-container { background-color:#0f172a !important; color:#e2e8f0 !important; }
    footer { text-align:center; padding:2rem; color:#aab3c2; font-size:1.2rem; font-weight:600; margin-top:2rem; }
    .left-box {
        background: radial-gradient(circle at top left, #0f172a, #1e293b);
        border-radius:20px; padding:3rem 2rem; color:#f1f5f9; box-shadow:6px 0 24px rgba(0,0,0,0.4);
    }
    .right-box {
        background:linear-gradient(180deg,#1e293b,#0f172a);
        border-radius:20px; padding:2rem; box-shadow:-6px 0 24px rgba(0,0,0,0.35);
    }
    .stButton > button {
        border:none !important; cursor:pointer;
        padding:14px 28px !important; font-size:18px !important; font-weight:700 !important;
        border-radius:14px !important; color:#fff !important;
        background:linear-gradient(180deg,#4ea3ff 0%,#2f86ff 60%,#0f6fff 100%) !important;
        box-shadow:0 8px 24px rgba(15,111,255,0.35);
    }
    a.macbtn {
        display:inline-block; text-decoration:none !important; color:#fff !important;
        padding:10px 22px; font-weight:700; border-radius:12px;
        background:linear-gradient(180deg,#4ea3ff 0%,#2f86ff 60%,#0f6fff 100%);
    }
    /* Larger workflow tabs */
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
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────
# QUERY PARAM ROUTING (modern API)
# ────────────────────────────────
try:
    qp = st.query_params
except Exception:
    qp = {}

if "stage" in qp:
    target = qp["stage"]
    if target in {"landing", "agents", "login", "credit_agent"} and st.session_state.stage != target:
        st.session_state.stage = target
        _clear_qp()
        st.rerun()

if "launch" in qp or ("agent" in qp and qp.get("agent") == ["credit"]):
    st.session_state.stage = "login"
    _clear_qp()
    st.rerun()

# ────────────────────────────────
# STAGE: LANDING
# ────────────────────────────────
if st.session_state.stage == "landing":
    c1, c2 = st.columns([1.1, 1.9], gap="large")
    with c1:
        st.markdown("<div class='left-box'>", unsafe_allow_html=True)
        logo_path = load_image("people_logo")
        if logo_path:
            st.image(logo_path, width=160)
        else:
            up = st.file_uploader("Upload People Logo", type=["jpg", "png", "webp"], key="upload_logo")
            if up:
                save_uploaded_image(up, "people_logo")
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
            st.session_state.stage = "agents"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='right-box'>", unsafe_allow_html=True)
        st.markdown("<h2>📊 Global AI Agent Library</h2>", unsafe_allow_html=True)
        rows = []
        for sector, industry, agent, desc, status, emoji in AGENTS:
            rows.append({
                "🖼️": render_image_tag(agent, industry, emoji),
                "🏭 Sector": sector,
                "🧩 Industry": industry,
                "🤖 Agent": agent,
                "🧠 Description": desc,
                "📶 Status": f'<span style="color:{"#22c55e" if status=="Available" else "#f59e0b"};">{status}</span>'
            })
        st.write(pd.DataFrame(rows).to_html(escape=False, index=False), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<footer>Made with ❤️ by Dzoan Nguyen — Open AI Sandbox Initiative</footer>", unsafe_allow_html=True)
    st.stop()

# ────────────────────────────────
# STAGE: AGENTS
# ────────────────────────────────
if st.session_state.stage == "agents":
    top = st.columns([1, 4, 1])
    with top[0]:
        if st.button("⬅️ Back to Home", key="btn_back_home_from_agents"):
            st.session_state.stage = "landing"
            st.rerun()
    with top[1]:
        st.title("🤖 Available AI Agents")

    df = pd.DataFrame([
        {"Agent": "💳 Credit Appraisal Agent",
         "Description": "Explainable AI for retail loan decisioning",
         "Status": "✅ Available",
         "Action": '<a class="macbtn" href="?agent=credit&stage=login">🚀 Launch</a>'},
        {"Agent": "🏦 Asset Appraisal Agent",
         "Description": "Market-driven collateral valuation",
         "Status": "🕓 Coming Soon", "Action": "—"},
    ])
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
    st.markdown("<footer>Made with ❤️ by Dzoan Nguyen — Open AI Sandbox Initiative</footer>", unsafe_allow_html=True)
    st.stop()
