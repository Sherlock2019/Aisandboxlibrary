from __future__ import annotations

import datetime as dt
import io
import json
import os
from typing import Any, Dict, List

import pandas as pd
import requests
import streamlit as st

from lib import (
    API_URL,
    CURRENCY_OPTIONS,
    PAGES,
    TMP_FEEDBACK_DIR,
    apply_form_styles,
    append_user_info,
    build_training_payload,
    dedupe_columns,
    drop_pii_columns,
    ensure_currency_defaults,
    ensure_session_defaults,
    fmt_currency_label,
    generate_anon_synthetic,
    generate_raw_synthetic,
    render_credit_dashboard,
    save_to_runs,
    set_active_page,
    show_footer,
    strip_policy_banned,
    to_agent_schema,
    try_json,
)

ensure_session_defaults()
ensure_currency_defaults()
if not st.session_state.logged_in:
    set_active_page("Login")
    st.switch_page(PAGES["Login"])
    st.stop()

apply_form_styles(include_download=True)
set_active_page("CreditApp")

cols = st.columns([1, 4, 1])
with cols[0]:
    if st.button("⬅️ Back to Home", key="btn_back_home_from_credit"):
        set_active_page("Landing")
        st.switch_page(PAGES["Landing"])
with cols[1]:
    st.title("💳 AI Credit Appraisal Platform")
    st.caption("Generate, sanitize, and appraise credit with AI agent power and human insight.")

LLM_MODELS = [
    ("Phi-3 Mini (3.8B) — CPU OK", "phi3:3.8b", "CPU 8GB RAM (fast)"),
    ("Mistral 7B Instruct — CPU slow / GPU OK", "mistral:7b-instruct", "CPU 16GB (slow) or GPU ≥8GB"),
    ("Gemma-2 7B — CPU slow / GPU OK", "gemma2:7b", "CPU 16GB (slow) or GPU ≥8GB"),
    ("LLaMA-3 8B — GPU recommended", "llama3:8b-instruct", "GPU ≥12GB (CPU very slow)"),
    ("Qwen2 7B — GPU recommended", "qwen2:7b-instruct", "GPU ≥12GB (CPU very slow)"),
    ("Mixtral 8x7B — GPU only (big)", "mixtral:8x7b-instruct", "GPU 24–48GB"),
]
LLM_LABELS = [label for (label, _, _) in LLM_MODELS]
LLM_VALUE_BY_LABEL = {label: value for (label, value, _) in LLM_MODELS}
LLM_HINT_BY_LABEL = {label: hint for (label, _, hint) in LLM_MODELS}

OPENSTACK_FLAVORS = {
    "m4.medium": "4 vCPU / 8 GB RAM — CPU-only small",
    "m8.large": "8 vCPU / 16 GB RAM — CPU-only medium",
    "g1.a10.1": "8 vCPU / 32 GB RAM + 1×A10 24GB",
    "g1.l40.1": "16 vCPU / 64 GB RAM + 1×L40 48GB",
    "g2.a100.1": "24 vCPU / 128 GB RAM + 1×A100 80GB",
}

CLASSIC_DEFAULTS = {
    "max_dti": 0.45,
    "min_emp_years": 2,
    "min_credit_hist": 3,
    "salary_floor": 3000,
    "max_delinquencies": 2,
    "max_current_loans": 3,
    "req_min": 1000,
    "req_max": 200000,
    "loan_terms": [12, 24, 36, 48, 60],
    "threshold": 0.45,
    "target_rate": None,
    "random_band": True,
    "min_income_debt_ratio": 0.35,
    "compounded_debt_factor": 1.0,
    "monthly_debt_relief": 0.50,
}
NDI_DEFAULTS = {
    "ndi_value": 800.0,
    "ndi_ratio": 0.50,
    "threshold": 0.45,
    "target_rate": None,
    "random_band": True,
}

if "classic_rules" not in st.session_state:
    st.session_state.classic_rules = CLASSIC_DEFAULTS.copy()
if "ndi_rules" not in st.session_state:
    st.session_state.ndi_rules = NDI_DEFAULTS.copy()


def reset_classic() -> None:
    st.session_state.classic_rules = CLASSIC_DEFAULTS.copy()


def reset_ndi() -> None:
    st.session_state.ndi_rules = NDI_DEFAULTS.copy()


def prep_and_pack(df: pd.DataFrame, filename: str) -> Dict[str, Any]:
    safe_df = dedupe_columns(df)
    safe_df, _ = drop_pii_columns(safe_df)
    safe_df = strip_policy_banned(safe_df)
    safe_df = to_agent_schema(safe_df)
    buffer = io.StringIO()
    safe_df.to_csv(buffer, index=False)
    return {"file": (filename, buffer.getvalue().encode("utf-8"), "text/csv")}

try:
    resp = requests.get(f"{API_URL}/v1/training/production_meta", timeout=5)
    if resp.status_code == 200:
        meta = resp.json()
        if meta.get("has_production"):
            ver = (meta.get("meta") or {}).get("version", "1.x")
            src = (meta.get("meta") or {}).get("source", "production")
            st.success(f"🟢 Production model active — version: {ver} • source: {src}")
        else:
            st.warning("⚠️ No production model promoted yet — using baseline.")
    else:
        st.info("ℹ️ Could not fetch production model meta.")
except Exception:  # noqa: BLE001
    st.info("ℹ️ Production meta unavailable.")

trained_dir = os.path.expanduser("~/credit-appraisal-agent-poc/agents/credit_appraisal/models/trained")
models: List[Any] = []
if os.path.exists(trained_dir):
    for file in os.listdir(trained_dir):
        if file.endswith(".joblib"):
            path = os.path.join(trained_dir, file)
            created = dt.datetime.fromtimestamp(os.path.getctime(path)).strftime("%b %d, %Y %H:%M")
            models.append((file, path, created))

if models:
    models.sort(key=lambda item: item[2], reverse=True)
    display_names = [f"{name} — {created}" for (name, _, created) in models]
    selected_display = st.selectbox("📦 Select trained model to use", display_names)
    selected_model = models[display_names.index(selected_display)][1]
    st.success(f"✅ Using model: {os.path.basename(selected_model)}")
    st.session_state["selected_trained_model"] = selected_model
    if st.button("🚀 Promote this model to Production"):
        prod_path = os.path.expanduser(
            "~/credit-appraisal-agent-poc/agents/credit_appraisal/models/production/model.joblib"
        )
        os.makedirs(os.path.dirname(prod_path), exist_ok=True)
        import shutil

        shutil.copy2(selected_model, prod_path)
        st.success(f"✅ Model promoted to production: {os.path.basename(prod_path)}")
else:
    st.warning("⚠️ No trained models found — train one in Step 5 first.")

with st.expander("🧠 Local LLM & Hardware Profile", expanded=True):
    c1, c2 = st.columns([1.2, 1])
    with c1:
        model_label = st.selectbox("Local LLM (used for narratives/explanations)", LLM_LABELS, index=1)
        llm_value = LLM_VALUE_BY_LABEL[model_label]
        st.caption(f"Hint: {LLM_HINT_BY_LABEL[model_label]}")
    with c2:
        flavor = st.selectbox("OpenStack flavor / host profile", list(OPENSTACK_FLAVORS.keys()), index=0)
        st.caption(OPENSTACK_FLAVORS[flavor])
    st.caption("These are passed to the API as hints; your API can choose Ollama/Flowise backends accordingly.")


tab_gen, tab_clean, tab_run, tab_review, tab_train = st.tabs(
    [
        "🏦 Synthetic Data Generator",
        "🧹 Anonymize & Sanitize Data",
        "🤖 Credit appraisal by AI assistant",
        "🧑‍⚖️ Human Review",
        "🔁 Training (Feedback → Retrain)",
    ]
)

with tab_gen:
    st.subheader("🏦 Synthetic Credit Data Generator")
    c1, c2 = st.columns([1, 2])
    with c1:
        code = st.selectbox(
            "Currency",
            list(CURRENCY_OPTIONS.keys()),
            index=list(CURRENCY_OPTIONS.keys()).index(st.session_state["currency_code"]),
            help="All monetary fields will be in this local currency.",
        )
        if code != st.session_state["currency_code"]:
            st.session_state["currency_code"] = code
            ensure_currency_defaults()
    with c2:
        st.info(f"Amounts will be generated in **{st.session_state['currency_label']}**.", icon="💰")

    rows = st.slider("Number of rows to generate", 50, 2000, 200, step=50)
    non_bank_ratio = st.slider("Share of non-bank customers", 0.0, 1.0, 0.30, 0.05)

    colA, colB = st.columns(2)
    with colA:
        if st.button("🔴 Generate RAW Synthetic Data (with PII)", use_container_width=True):
            raw_df = append_user_info(generate_raw_synthetic(rows, non_bank_ratio))
            st.session_state.synthetic_raw_df = raw_df
            raw_path = save_to_runs(raw_df, "synthetic_raw")
            st.success(
                f"Generated RAW (PII) dataset with {rows} rows in {st.session_state['currency_label']}. Saved to {raw_path}"
            )
            st.dataframe(raw_df.head(10), use_container_width=True)
            st.download_button(
                "⬇️ Download RAW CSV",
                raw_df.to_csv(index=False).encode("utf-8"),
                os.path.basename(raw_path),
                "text/csv",
            )

    with colB:
        if st.button("🟢 Generate ANON Synthetic Data (ready for agent)", use_container_width=True):
            anon_df = append_user_info(generate_anon_synthetic(rows, non_bank_ratio))
            st.session_state.synthetic_df = anon_df
            anon_path = save_to_runs(anon_df, "synthetic_anon")
            st.success(
                f"Generated ANON dataset with {rows} rows in {st.session_state['currency_label']}. Saved to {anon_path}"
            )
            st.dataframe(anon_df.head(10), use_container_width=True)
            st.download_button(
                "⬇️ Download ANON CSV",
                anon_df.to_csv(index=False).encode("utf-8"),
                os.path.basename(anon_path),
                "text/csv",
            )

with tab_clean:
    st.subheader("🧹 Upload & Anonymize Customer Data (PII columns will be DROPPED)")
    st.markdown("Upload your **real CSV**. We drop PII columns and scrub emails/phones in text fields.")

    uploaded = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not read CSV: {exc}")
            st.stop()

        st.write("📊 Original Data Preview:")
        st.dataframe(dedupe_columns(df.head(5)), use_container_width=True)

        sanitized, dropped_cols = drop_pii_columns(df)
        sanitized = append_user_info(sanitized)
        sanitized = dedupe_columns(sanitized)
        st.session_state.anonymized_df = sanitized

        st.success(f"Dropped PII columns: {sorted(dropped_cols) if dropped_cols else 'None'}")
        st.write("✅ Sanitized Data Preview:")
        st.dataframe(sanitized.head(5), use_container_width=True)

        fpath = save_to_runs(sanitized, "anonymized")
        st.success(f"Saved anonymized file: {fpath}")
        st.download_button(
            "⬇️ Download Clean Data",
            sanitized.to_csv(index=False).encode("utf-8"),
            os.path.basename(fpath),
            "text/csv",
        )
    else:
        st.info("Choose a CSV to see the sanitize flow.", icon="ℹ️")

with tab_run:
    st.subheader("🤖 Credit appraisal by AI assistant")
    st.markdown('<a name="credit-appraisal-stage"></a>', unsafe_allow_html=True)

    data_choice = st.selectbox(
        "Select Data Source",
        [
            "Use synthetic (ANON)",
            "Use synthetic (RAW – auto-sanitize)",
            "Use anonymized dataset",
            "Upload manually",
        ],
    )
    use_llm = st.checkbox("Use LLM narrative", value=False)

    if data_choice == "Upload manually":
        up = st.file_uploader("Upload your CSV", type=["csv"], key="manual_upload_run_file")
        if up is not None:
            st.session_state["manual_upload_name"] = up.name
            st.session_state["manual_upload_bytes"] = up.getvalue()
            st.success(
                f"File staged: {up.name} ({len(st.session_state['manual_upload_bytes'])} bytes)"
            )

    rule_mode = st.radio(
        "Choose rule mode",
        ["Classic (bank-style metrics)", "NDI (Net Disposable Income) — simple"],
        index=0,
        help="NDI = income - all monthly obligations. Approve if NDI and NDI ratio pass thresholds.",
    )

    if rule_mode.startswith("Classic"):
        with st.expander("Classic Metrics (with Reset)", expanded=True):
            rc = st.session_state.classic_rules
            r1, r2, r3 = st.columns(3)
            with r1:
                rc["max_dti"] = st.slider("Max Debt-to-Income (DTI)", 0.0, 1.0, rc["max_dti"], 0.01)
                rc["min_emp_years"] = st.number_input("Min Employment Years", 0, 40, rc["min_emp_years"])
                rc["min_credit_hist"] = st.number_input("Min Credit History (years)", 0, 40, rc["min_credit_hist"])
            with r2:
                rc["salary_floor"] = st.number_input(
                    "Minimum Monthly Salary",
                    0,
                    1_000_000_000,
                    rc["salary_floor"],
                    step=1000,
                    help=fmt_currency_label("in local currency"),
                )
                rc["max_delinquencies"] = st.number_input("Max Delinquencies", 0, 10, rc["max_delinquencies"])
                rc["max_current_loans"] = st.number_input("Max Current Loans", 0, 10, rc["max_current_loans"])
            with r3:
                rc["req_min"] = st.number_input(
                    fmt_currency_label("Requested Amount Min"),
                    0,
                    10_000_000_000,
                    rc["req_min"],
                    step=1000,
                )
                rc["req_max"] = st.number_input(
                    fmt_currency_label("Requested Amount Max"),
                    0,
                    10_000_000_000,
                    rc["req_max"],
                    step=1000,
                )
                rc["loan_terms"] = st.multiselect(
                    "Allowed Loan Terms (months)",
                    [12, 24, 36, 48, 60, 72],
                    default=rc["loan_terms"],
                )

            st.markdown("#### 🧮 Debt Pressure Controls")
            d1, d2, d3 = st.columns(3)
            with d1:
                rc["min_income_debt_ratio"] = st.slider(
                    "Min Income / (Compounded Debt) Ratio",
                    0.10,
                    2.00,
                    rc["min_income_debt_ratio"],
                    0.01,
                )
            with d2:
                rc["compounded_debt_factor"] = st.slider(
                    "Compounded Debt Factor (× requested)", 0.5, 3.0, rc["compounded_debt_factor"], 0.1
                )
            with d3:
                rc["monthly_debt_relief"] = st.slider(
                    "Monthly Debt Relief Factor", 0.10, 1.00, rc["monthly_debt_relief"], 0.05
                )

            st.markdown("---")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                use_target = st.toggle("🎯 Use target approval rate", value=(rc["target_rate"] is not None))
            with c2:
                rc["random_band"] = st.toggle(
                    "🎲 Randomize approval band (20–60%) when no target", value=rc["random_band"]
                )
            with c3:
                if st.button("↩️ Reset to defaults"):
                    reset_classic()
                    st.experimental_rerun()

            if use_target:
                rc["target_rate"] = st.slider(
                    "Target approval rate", 0.05, 0.95, rc["target_rate"] or 0.40, 0.01
                )
                rc["threshold"] = None
            else:
                rc["threshold"] = st.slider("Model score threshold", 0.0, 1.0, rc["threshold"], 0.01)
                rc["target_rate"] = None
    else:
        with st.expander("NDI Metrics (with Reset)", expanded=True):
            rn = st.session_state.ndi_rules
            n1, n2 = st.columns(2)
            with n1:
                rn["ndi_value"] = st.number_input(
                    fmt_currency_label("Min NDI (Net Disposable Income) per month"),
                    0.0,
                    1e12,
                    float(rn["ndi_value"]),
                    step=50.0,
                )
            with n2:
                rn["ndi_ratio"] = st.slider("Min NDI / Income ratio", 0.0, 1.0, float(rn["ndi_ratio"]), 0.01)
            st.caption("NDI = income - all monthly obligations (rent, food, loans, cards, etc.).")

            st.markdown("---")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                use_target = st.toggle("🎯 Use target approval rate", value=(rn["target_rate"] is not None))
            with c2:
                rn["random_band"] = st.toggle(
                    "🎲 Randomize approval band (20–60%) when no target", value=rn["random_band"]
                )
            with c3:
                if st.button("↩️ Reset to defaults (NDI)"):
                    reset_ndi()
                    st.experimental_rerun()

            if use_target:
                rn["target_rate"] = st.slider(
                    "Target approval rate", 0.05, 0.95, rn["target_rate"] or 0.40, 0.01
                )
                rn["threshold"] = None
            else:
                rn["threshold"] = st.slider("Model score threshold", 0.0, 1.0, rn["threshold"], 0.01)
                rn["target_rate"] = None

    if st.button("🚀 Run Agent", use_container_width=True):
        data: Dict[str, Any] = {
            "use_llm_narrative": str(use_llm).lower(),
            "llm_model": llm_value,
            "hardware_flavor": flavor,
            "currency_code": st.session_state["currency_code"],
            "currency_symbol": st.session_state["currency_symbol"],
        }
        if rule_mode.startswith("Classic"):
            rc = st.session_state.classic_rules
            data.update(
                {
                    "min_employment_years": str(rc["min_emp_years"]),
                    "max_debt_to_income": str(rc["max_dti"]),
                    "min_credit_history_length": str(rc["min_credit_hist"]),
                    "max_num_delinquencies": str(rc["max_delinquencies"]),
                    "max_current_loans": str(rc["max_current_loans"]),
                    "requested_amount_min": str(rc["req_min"]),
                    "requested_amount_max": str(rc["req_max"]),
                    "loan_term_months_allowed": ",".join(map(str, rc["loan_terms"])) if rc["loan_terms"] else "",
                    "min_income_debt_ratio": str(rc["min_income_debt_ratio"]),
                    "compounded_debt_factor": str(rc["compounded_debt_factor"]),
                    "monthly_debt_relief": str(rc["monthly_debt_relief"]),
                    "salary_floor": str(rc["salary_floor"]),
                    "threshold": "" if rc["threshold"] is None else str(rc["threshold"]),
                    "target_approval_rate": "" if rc["target_rate"] is None else str(rc["target_rate"]),
                    "random_band": str(rc["random_band"]).lower(),
                    "random_approval_band": str(rc["random_band"]).lower(),
                    "rule_mode": "classic",
                }
            )
        else:
            rn = st.session_state.ndi_rules
            data.update(
                {
                    "ndi_value": str(rn["ndi_value"]),
                    "ndi_ratio": str(rn["ndi_ratio"]),
                    "threshold": "" if rn["threshold"] is None else str(rn["threshold"]),
                    "target_approval_rate": "" if rn["target_rate"] is None else str(rn["target_rate"]),
                    "random_band": str(rn["random_band"]).lower(),
                    "random_approval_band": str(rn["random_band"]).lower(),
                    "rule_mode": "ndi",
                }
            )

        try:
            files: Dict[str, Any] | None = None
            if data_choice == "Use synthetic (ANON)":
                if "synthetic_df" not in st.session_state:
                    st.warning("No ANON synthetic dataset found. Generate it in the first tab.")
                    st.stop()
                files = prep_and_pack(st.session_state.synthetic_df, "synthetic_anon.csv")
            elif data_choice == "Use synthetic (RAW – auto-sanitize)":
                if "synthetic_raw_df" not in st.session_state:
                    st.warning("No RAW synthetic dataset found. Generate it in the first tab.")
                    st.stop()
                files = prep_and_pack(st.session_state.synthetic_raw_df, "synthetic_raw_sanitized.csv")
            elif data_choice == "Use anonymized dataset":
                if "anonymized_df" not in st.session_state:
                    st.warning("No anonymized dataset found. Create it in the second tab.")
                    st.stop()
                files = prep_and_pack(st.session_state.anonymized_df, "anonymized.csv")
            elif data_choice == "Upload manually":
                up_name = st.session_state.get("manual_upload_name")
                up_bytes = st.session_state.get("manual_upload_bytes")
                if not up_name or not up_bytes:
                    st.warning("Please upload a CSV first.")
                    st.stop()
                try:
                    tmp_df = pd.read_csv(io.BytesIO(up_bytes))
                    files = prep_and_pack(tmp_df, up_name)
                except Exception:
                    files = {"file": (up_name, up_bytes, "text/csv")}
            else:
                st.error("Unknown data source selection.")
                st.stop()

            response = requests.post(
                f"{API_URL}/v1/agents/credit_appraisal/run", data=data, files=files, timeout=180
            )
            if response.status_code != 200:
                st.error(f"Run failed ({response.status_code}): {response.text}")
                st.stop()

            res = response.json()
            st.session_state.last_run_id = res.get("run_id")
            st.success(f"✅ Run succeeded! Run ID: {st.session_state.last_run_id}")

            merged_url = f"{API_URL}/v1/runs/{st.session_state.last_run_id}/report?format=csv"
            merged_bytes = requests.get(merged_url, timeout=30).content
            merged_df = pd.read_csv(io.BytesIO(merged_bytes))
            st.session_state["last_merged_df"] = merged_df

            st.markdown("### 📄 Credit Ai Agent  Decisions Table (filtered)")
            uniq_dec = sorted(
                [d for d in merged_df.get("decision", pd.Series(dtype=str)).dropna().unique()]
            )
            chosen = st.multiselect(
                "Filter decision", options=uniq_dec, default=uniq_dec, key="filter_decisions"
            )
            df_view = merged_df.copy()
            if "decision" in df_view.columns and chosen:
                df_view = df_view[df_view["decision"].isin(chosen)]
            st.dataframe(df_view, use_container_width=True)

            st.markdown("## 📊 Dashboard")
            render_credit_dashboard(merged_df, st.session_state.get("currency_symbol", ""))

            if "rule_reasons" in df_view.columns:
                rule_json = df_view["rule_reasons"].apply(try_json)
                df_view["metrics_met"] = rule_json.apply(
                    lambda data: ", ".join(sorted([k for k, v in (data or {}).items() if v is True]))
                    if isinstance(data, dict)
                    else ""
                )
                df_view["metrics_unmet"] = rule_json.apply(
                    lambda data: ", ".join(sorted([k for k, v in (data or {}).items() if v is False]))
                    if isinstance(data, dict)
                    else ""
                )
            cols_show = [
                c
                for c in [
                    "application_id",
                    "customer_type",
                    "decision",
                    "score",
                    "loan_amount",
                    "income",
                    "metrics_met",
                    "metrics_unmet",
                    "proposed_loan_option",
                    "proposed_consolidation_loan",
                    "top_feature",
                    "explanation",
                ]
                if c in df_view.columns
            ]
            st.dataframe(df_view[cols_show].head(500), use_container_width=True)

            ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            out_name = f"ai-appraisal-outputs-{ts}-{st.session_state['currency_code']}.csv"
            csv_data = merged_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download AI Outputs For Human Review (CSV)",
                csv_data,
                file_name=out_name,
                mime="text/csv",
                use_container_width=True,
            )

        except Exception as exc:  # noqa: BLE001
            st.exception(exc)

    if st.session_state.get("last_run_id"):
        st.markdown("---")
        st.subheader("📥 Download Latest Outputs")
        rid = st.session_state.last_run_id
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"[⬇️ PDF]({API_URL}/v1/runs/{rid}/report?format=pdf)")
        with col2:
            st.markdown(f"[⬇️ Scores CSV]({API_URL}/v1/runs/{rid}/report?format=scores_csv)")
        with col3:
            st.markdown(f"[⬇️ Explanations CSV]({API_URL}/v1/runs/{rid}/report?format=explanations_csv)")
        with col4:
            st.markdown(f"[⬇️ Merged CSV]({API_URL}/v1/runs/{rid}/report?format=csv)")
        with col5:
            st.markdown(f"[⬇️ JSON]({API_URL}/v1/runs/{rid}/report?format=json)")

with tab_review:
    st.subheader(
        "🧑‍⚖️ Human Review — Correct AI Decisions & Score Agreement > Drop your AI appraisal output CSV from previous Stage  below"
    )

    uploaded_review = st.file_uploader(
        "Load AI outputs CSV for review (optional)", type=["csv"], key="review_csv_loader"
    )
    if uploaded_review is not None:
        try:
            st.session_state["last_merged_df"] = pd.read_csv(uploaded_review)
            st.success("Loaded review dataset from uploaded CSV.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not read uploaded CSV: {exc}")

    if "last_merged_df" not in st.session_state:
        st.info("Run the agent (previous tab) or upload an AI outputs CSV to load results for review.")
    else:
        dfm = st.session_state["last_merged_df"].copy()
        st.markdown("#### 1) Select rows to review and correct")

        editable_cols = []
        if "decision" in dfm.columns:
            editable_cols.append("decision")
        if "rule_reasons" in dfm.columns:
            editable_cols.append("rule_reasons")
        if "customer_type" in dfm.columns:
            editable_cols.append("customer_type")

        editable = dfm[["application_id"] + editable_cols].copy()
        editable.rename(columns={"decision": "ai_decision"}, inplace=True)
        editable["human_decision"] = editable.get("ai_decision", "approved")
        editable["human_rule_reasons"] = editable.get("rule_reasons", "")

        edited = st.data_editor(
            editable,
            num_rows="dynamic",
            use_container_width=True,
            key="review_editor",
            column_config={
                "human_decision": st.column_config.SelectboxColumn(options=["approved", "denied"]),
                "customer_type": st.column_config.SelectboxColumn(options=["bank", "non-bank"], disabled=True),
            },
        )

        st.markdown("#### 2) Compute agreement score")
        if st.button("Compute agreement score"):
            if "ai_decision" in edited.columns and "human_decision" in edited.columns:
                agree = (edited["ai_decision"] == edited["human_decision"]).astype(int)
                score = float(agree.mean()) if len(agree) else 0.0
                st.session_state["last_agreement_score"] = score

                import plotly.graph_objects as go

                fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=score * 100,
                        number={"suffix": "%", "font": {"size": 72, "color": "#f8fafc", "family": "Arial Black"}},
                        title={"text": "AI ↔ Human Agreement", "font": {"size": 28, "color": "#93c5fd", "family": "Arial"}},
                        gauge={
                            "axis": {"range": [0, 100], "tickwidth": 2, "tickcolor": "#f8fafc"},
                            "bar": {"color": "#3b82f6", "thickness": 0.3},
                            "bgcolor": "#1e293b",
                            "borderwidth": 2,
                            "bordercolor": "#334155",
                            "steps": [
                                {"range": [0, 50], "color": "#ef4444"},
                                {"range": [50, 75], "color": "#f59e0b"},
                                {"range": [75, 100], "color": "#22c55e"},
                            ],
                        },
                    )
                )
                fig.update_layout(
                    paper_bgcolor="#0f172a",
                    plot_bgcolor="#0f172a",
                    height=400,
                    margin=dict(t=60, b=20, l=60, r=60),
                )
                st.plotly_chart(fig, use_container_width=True)

                mismatched = edited[edited["ai_decision"] != edited["human_decision"]].copy()
                total = len(edited)
                disagree = len(mismatched)

                if disagree > 0:
                    st.markdown(
                        f"### ❌ {disagree} loans disagreed out of {total} ({(disagree/total)*100:.1f}% disagreement rate)"
                    )

                    def parse_ai_reason(text: str) -> str:
                        if not isinstance(text, str):
                            return "No metrics available"
                        try:
                            data = json.loads(text.replace("'", '"'))
                        except Exception:
                            return "Unreadable metrics"
                        passed = [k for k, v in data.items() if v is True]
                        failed = [k for k, v in data.items() if v is False]
                        parts: List[str] = []
                        if passed:
                            parts.append("✅ Pass: " + ", ".join(passed))
                        if failed:
                            parts.append("❌ Fail: " + ", ".join(failed))
                        return " | ".join(parts) if parts else "No metrics recorded"

                    mismatched["ai_metrics"] = (
                        mismatched["rule_reasons"].apply(parse_ai_reason)
                        if "rule_reasons" in mismatched
                        else "No data"
                    )
                    mismatched["human_reason"] = mismatched.get(
                        "human_rule_reasons", "Manual review adjustment"
                    )

                    def highlight(row: pd.Series) -> List[str]:
                        ai_color = "background-color: #ef4444; color: white;"
                        human_color = "background-color: #22c55e; color: black;"
                        return [
                            ai_color if col == "ai_decision" else human_color if col == "human_decision" else ""
                            for col in row.index
                        ]

                    show_cols = [
                        col
                        for col in [
                            "application_id",
                            "ai_decision",
                            "human_decision",
                            "ai_metrics",
                            "human_reason",
                        ]
                        if col in mismatched.columns
                    ]
                    styled_df = mismatched[show_cols].style.apply(highlight, axis=1)
                    st.dataframe(styled_df, use_container_width=True, height=420)
                else:
                    st.success("✅ Full agreement — no human-AI mismatches found.")
            else:
                st.warning("Missing decision columns to compute score.")

        st.markdown("#### 3) Export Human review CSV for Next Step : Training and loopback ")
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_user = st.session_state["user_info"]["name"].replace(" ", "").lower()
        review_name = f"creditappraisal.{safe_user}.production.{ts}.csv"
        csv_bytes = edited.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export review CSV", csv_bytes, review_name, "text/csv")
        st.caption(f"Saved file name pattern: **{review_name}**")

with tab_train:
    st.subheader("🔁 From Human Feedback CSV → Train and Promote Trained Model to Production Model ")
    st.markdown("**Drag & drop** one or more review CSVs exported from the Human Review tab.")
    up_list = st.file_uploader(
        "Upload feedback CSV(s)", type=["csv"], accept_multiple_files=True, key="train_feedback_uploader"
    )

    staged_paths: List[str] = []
    if up_list:
        for up in up_list:
            dest = os.path.join(TMP_FEEDBACK_DIR, up.name)
            with open(dest, "wb") as f:
                f.write(up.getvalue())
            staged_paths.append(dest)
        st.success(f"Staged {len(staged_paths)} feedback file(s) to {TMP_FEEDBACK_DIR}")
        st.write(staged_paths)

    payload = build_training_payload(staged_paths)
    st.code(json.dumps(payload, indent=2), language="json")

    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("🚀 Train candidate model"):
            try:
                resp = requests.post(f"{API_URL}/v1/training/train", json=payload, timeout=90)
                if resp.ok:
                    st.success(resp.json())
                    st.session_state["last_train_job"] = resp.json().get("job_id")
                else:
                    st.error(resp.text)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Train failed: {exc}")
    with colB:
        if st.button("⬆️ Promote last candidate to PRODUCTION"):
            try:
                resp = requests.post(f"{API_URL}/v1/training/promote", timeout=30)
                st.write(resp.json() if resp.ok else resp.text)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Promote failed: {exc}")

    st.markdown("---")
    st.markdown("### 💳 Loop back to Step 3 — Credit Appraisal Agent")
    st.caption("After retraining, return to the Credit Appraisal tab and use your new production model.")
    st.markdown(
        """
        <a href="?page=CreditApp" target="_self">
            <button style="
                background-color:#2563eb;
                color:white;
                border:none;
                border-radius:8px;
                padding:12px 24px;
                font-size:16px;
                font-weight:600;
                cursor:pointer;
                width:100%;
                box-shadow:0px 0px 6px rgba(37,99,235,0.5);
            ">⬅️ Go Back to Step 3 and Use New Model</button>
        </a>
        """,
        unsafe_allow_html=True,
    )

show_footer()
