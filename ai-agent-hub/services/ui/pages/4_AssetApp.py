import streamlit as st
import requests

st.set_page_config(page_title="🏛️ Asset Appraisal", layout="wide")
st.title("🏛️ Asset Appraisal Agent")

API_URL = "http://localhost:8090/run/asset_appraisal"

st.markdown("Estimate **asset value** based on AI model inference from your local agent.")

asset = st.text_input("🏠 Describe asset", "Villa in District 2, Saigon")

if st.button("📈 Estimate Value"):
    try:
        res = requests.post(API_URL, json={"asset": asset}, timeout=10)
        r = res.json()
        st.success(f"Estimated Value: ${r.get('estimated_value', 0):,.0f}")
        st.metric("Confidence", f"{r.get('confidence', 0)*100:.1f}%")
    except Exception as e:
        st.error(f"API error: {e}")
