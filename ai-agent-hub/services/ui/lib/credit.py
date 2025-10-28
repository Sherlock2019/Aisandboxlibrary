"""Credit appraisal utilities shared across Streamlit pages."""
from __future__ import annotations

import datetime as _dt
import io
import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

from .app_state import RUNS_DIR


BANNED_NAMES = {"race", "gender", "religion", "ethnicity", "ssn", "national_id"}
PII_COLS = {"customer_name", "name", "email", "phone", "address", "ssn", "national_id", "dob"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\-\s]{6,}\d")

CURRENCY_OPTIONS = {
    "USD": ("USD $", "$", 1.0),
    "EUR": ("EUR €", "€", 0.93),
    "GBP": ("GBP £", "£", 0.80),
    "JPY": ("JPY ¥", "¥", 150.0),
    "VND": ("VND ₫", "₫", 24000.0),
}


def ensure_currency_defaults() -> None:
    if "currency_code" not in st.session_state:
        st.session_state["currency_code"] = "USD"
    code = st.session_state["currency_code"]
    label, symbol, fx = CURRENCY_OPTIONS[code]
    st.session_state["currency_label"] = label
    st.session_state["currency_symbol"] = symbol
    st.session_state["currency_fx"] = fx


def dedupe_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.duplicated(keep="last")]


def scrub_text_pii(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    value = EMAIL_RE.sub("", value)
    value = PHONE_RE.sub("", value)
    return value.strip()


def drop_pii_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    original_cols = list(df.columns)
    keep_cols = [c for c in original_cols if all(k not in c.lower() for k in PII_COLS)]
    dropped = [c for c in original_cols if c not in keep_cols]
    result = df[keep_cols].copy()
    for col in result.select_dtypes(include="object"):
        result[col] = result[col].apply(scrub_text_pii)
    return dedupe_columns(result), dropped


def strip_policy_banned(df: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in df.columns if c.lower() not in BANNED_NAMES]
    return df[keep]


def append_user_info(df: pd.DataFrame) -> pd.DataFrame:
    meta = st.session_state.get("user_info", {})
    meta.setdefault("name", "")
    meta.setdefault("email", "")
    meta.setdefault("flagged", False)
    meta.setdefault("timestamp", _dt.datetime.utcnow().isoformat())
    result = df.copy()
    result["session_user_name"] = meta["name"]
    result["session_user_email"] = meta["email"]
    result["session_flagged"] = meta["flagged"]
    result["created_at"] = meta["timestamp"]
    return dedupe_columns(result)


def save_to_runs(df: pd.DataFrame, prefix: str) -> str:
    ts = _dt.datetime.now().strftime("%Y-%m-%d_%H-%M")
    flag_suffix = "_FLAGGED" if st.session_state.get("user_info", {}).get("flagged") else ""
    fname = f"{prefix}_{ts}{flag_suffix}.csv"
    path = os.path.join(RUNS_DIR, fname)
    dedupe_columns(df).to_csv(path, index=False)
    return path


def try_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def safe_json(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


def fmt_currency_label(base: str) -> str:
    symbol = st.session_state.get("currency_symbol", "")
    return f"{base} ({symbol})" if symbol else base


def _kpi_card(label: str, value: str, sublabel: Optional[str] = None) -> None:
    st.markdown(
        f"""
        <div style="background:#0e1117;border:1px solid #2a2f3e;border-radius:12px;padding:14px 16px;margin-bottom:10px;">
          <div style="font-size:12px;color:#9aa4b2;text-transform:uppercase;letter-spacing:.06em;">{label}</div>
          <div style="font-size:28px;font-weight:700;color:#e6edf3;line-height:1.1;margin-top:2px;">{value}</div>
          {f'<div style="font-size:12px;color:#9aa4b2;margin-top:6px;">{sublabel}</div>' if sublabel else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_credit_dashboard(df: pd.DataFrame, currency_symbol: str = "") -> None:
    if df is None or df.empty:
        st.info("No data to visualize yet.")
        return

    cols = df.columns

    st.markdown("## 🔝 Top 10 Snapshot")

    if {"decision", "loan_amount", "application_id"} <= set(cols):
        top_approved = df[df["decision"].astype(str).str.lower() == "approved"].copy()
        if not top_approved.empty:
            top_approved = top_approved.sort_values("loan_amount", ascending=False).head(10)
            fig = px.bar(
                top_approved,
                x="loan_amount",
                y="application_id",
                orientation="h",
                title="Top 10 Approved Loans",
                labels={"loan_amount": f"Loan Amount {currency_symbol}", "application_id": "Application"},
            )
            fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=420, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No approved loans available to show top 10.")

    if {"collateral_type", "collateral_value"} <= set(cols):
        cprof = df.groupby("collateral_type", dropna=False).agg(
            avg_value=("collateral_value", "mean"),
            cnt=("collateral_type", "count"),
        ).reset_index()
        if not cprof.empty:
            cprof = cprof.sort_values("avg_value", ascending=False).head(10)
            fig = px.bar(
                cprof,
                x="avg_value",
                y="collateral_type",
                orientation="h",
                title="Top 10 Collateral Types (Avg Value)",
                labels={"avg_value": f"Avg Value {currency_symbol}", "collateral_type": "Collateral Type"},
                hover_data=["cnt"],
            )
            fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=420, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    if "rule_reasons" in cols and "decision" in cols:
        denied = df[df["decision"].astype(str).str.lower() == "denied"].copy()
        reasons_count: Dict[str, int] = {}
        for _, row in denied.iterrows():
            rr = safe_json(row.get("rule_reasons"))
            for key, value in rr.items():
                if value is False:
                    reasons_count[key] = reasons_count.get(key, 0) + 1
        if reasons_count:
            items = pd.DataFrame(
                sorted(reasons_count.items(), key=lambda x: x[1], reverse=True),
                columns=["reason", "count"],
            ).head(10)
            fig = px.bar(
                items,
                x="count",
                y="reason",
                orientation="h",
                title="Top 10 Reasons for Denial",
                labels={"count": "Count", "reason": "Rule"},
            )
            fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=420, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No denial reasons detected.")

    officer_col = None
    for guess in ("loan_officer", "officer", "reviewed_by", "session_user_name"):
        if guess in cols:
            officer_col = guess
            break
    if officer_col and "decision" in cols:
        perf = (
            df.assign(is_approved=(df["decision"].astype(str).str.lower() == "approved").astype(int))
            .groupby(officer_col, dropna=False)["is_approved"]
            .agg(approved_rate="mean", n="count")
            .reset_index()
        )
        if not perf.empty:
            perf["approved_rate_pct"] = (perf["approved_rate"] * 100).round(1)
            perf = perf.sort_values(["approved_rate_pct", "n"], ascending=[False, False]).head(10)
            fig = px.bar(
                perf,
                x="approved_rate_pct",
                y=officer_col,
                orientation="h",
                title="Top 10 Loan Officer Approval Rate (this batch)",
                labels={"approved_rate_pct": "Approval Rate (%)", officer_col: "Officer"},
                hover_data=["n"],
            )
            fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=420, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("## 💡 Opportunities")

    opp_rows: List[Dict[str, Any]] = []
    if {"income", "loan_amount"}.issubset(cols):
        term_col = "loan_term_months" if "loan_term_months" in cols else (
            "loan_duration_months" if "loan_duration_months" in cols else None
        )
        if term_col:
            for _, row in df.iterrows():
                inc = float(row.get("income", 0) or 0)
                amt = float(row.get("loan_amount", 0) or 0)
                term = int(row.get(term_col, 0) or 0)
                dti = float(row.get("DTI", 0) or 0)
                if (term >= 36) and (amt <= inc * 0.8) and (dti <= 0.45):
                    opp_rows.append(
                        {
                            "application_id": row.get("application_id"),
                            "suggested_term": 24,
                            "loan_amount": amt,
                            "income": inc,
                            "DTI": dti,
                            "note": "Candidate for short-term plan (<=24m) based on affordability.",
                        }
                    )
    if opp_rows:
        st.markdown("#### 📎 Short-Term Loan Candidates")
        st.dataframe(pd.DataFrame(opp_rows).head(25), use_container_width=True, height=320)
    else:
        st.info("No short-term loan candidates identified in this batch.")

    st.markdown("#### 🔁 Buyback / Consolidation Beneficiaries")
    candidates: List[Dict[str, Any]] = []
    need = {"decision", "existing_debt", "loan_amount", "DTI"}
    if need <= set(cols):
        for _, row in df.iterrows():
            dec = str(row.get("decision", "")).lower()
            debt = float(row.get("existing_debt", 0) or 0)
            loan = float(row.get("loan_amount", 0) or 0)
            dti = float(row.get("DTI", 0) or 0)
            proposal = safe_json(row.get("proposed_consolidation_loan", {}))
            has_bb = bool(proposal)

            if dec == "denied" or dti > 0.45 or debt > loan:
                benefit_score = round((debt / (loan + 1e-6)) * 0.4 + dti * 0.6, 2)
                candidates.append(
                    {
                        "application_id": row.get("application_id"),
                        "customer_type": row.get("customer_type"),
                        "existing_debt": debt,
                        "loan_amount": loan,
                        "DTI": dti,
                        "collateral_type": row.get("collateral_type"),
                        "buyback_proposed": has_bb,
                        "buyback_amount": proposal.get("buyback_amount") if has_bb else None,
                        "benefit_score": benefit_score,
                        "note": proposal.get("note") if has_bb else None,
                    }
                )
    if candidates:
        cand_df = pd.DataFrame(candidates).sort_values("benefit_score", ascending=False)
        st.dataframe(cand_df.head(25), use_container_width=True, height=380)
    else:
        st.info("No additional buyback beneficiaries identified.")

    st.markdown("---")
    st.markdown("## 📈 Portfolio Snapshot")
    c1, c2, c3, c4 = st.columns(4)

    if "decision" in cols:
        total = len(df)
        approved = int((df["decision"].astype(str).str.lower() == "approved").sum())
        rate = (approved / total * 100) if total else 0.0
        with c1:
            _kpi_card("Approval Rate", f"{rate:.1f}%", f"{approved} of {total}")

    if {"decision", "loan_amount"} <= set(cols):
        ap = df[df["decision"].astype(str).str.lower() == "approved"]["loan_amount"]
        avg_amt = ap.mean() if len(ap) else 0.0
        with c2:
            _kpi_card("Avg Approved Amount", f"{currency_symbol}{avg_amt:,.0f}")

    if {"created_at", "decision_at"} <= set(cols):
        try:
            delta = (
                pd.to_datetime(df["decision_at"]) - pd.to_datetime(df["created_at"])
            ).dt.total_seconds() / 60.0
            avg_min = float(delta.mean())
            with c3:
                _kpi_card("Avg Decision Time", f"{avg_min:.1f} min")
        except Exception:
            with c3:
                _kpi_card("Avg Decision Time", "—")

    if "customer_type" in cols:
        nb = int((df["customer_type"].astype(str).str.lower() == "non-bank").sum())
        total = len(df)
        share = (nb / total * 100) if total else 0.0
        with c4:
            _kpi_card("Non-bank Share", f"{share:.1f}%", f"{nb} of {total}")

    st.markdown("## 🧭 Composition & Risk")

    if "decision" in cols:
        pie_df = df["decision"].value_counts().rename_axis("Decision").reset_index(name="Count")
        fig = px.pie(pie_df, names="Decision", values="Count", title="Decision Mix")
        fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=360, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    have_dti = "DTI" in cols
    have_ltv = "LTV" in cols
    if "decision" in cols and (have_dti or have_ltv):
        agg_map = {}
        if have_dti:
            agg_map["avg_DTI"] = ("DTI", "mean")
        if have_ltv:
            agg_map["avg_LTV"] = ("LTV", "mean")
        grp = df.groupby("decision").agg(**agg_map).reset_index()
        melted = grp.melt(id_vars=["decision"], var_name="metric", value_name="value")
        fig = px.bar(
            melted,
            x="decision",
            y="value",
            color="metric",
            barmode="group",
            title="Average DTI / LTV by Decision",
        )
        fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=360, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    term_col = "loan_term_months" if "loan_term_months" in cols else (
        "loan_duration_months" if "loan_duration_months" in cols else None
    )
    if term_col and "decision" in cols:
        mix = df.groupby([term_col, "decision"]).size().reset_index(name="count")
        fig = px.bar(
            mix,
            x=term_col,
            y="count",
            color="decision",
            title="Loan Term Mix",
            labels={term_col: "Term (months)", "count": "Count"},
            barmode="stack",
        )
        fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=360, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    if {"collateral_type", "collateral_value"} <= set(cols):
        cprof = df.groupby("collateral_type").agg(
            avg_col=("collateral_value", "mean"),
            cnt=("collateral_type", "count"),
        ).reset_index()
        fig = px.bar(
            cprof.sort_values("avg_col", ascending=False),
            x="collateral_type",
            y="avg_col",
            title=f"Avg Collateral Value by Type ({currency_symbol})",
            hover_data=["cnt"],
        )
        fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=360, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    if "proposed_loan_option" in cols:
        plans = df["proposed_loan_option"].dropna().astype(str)
        if len(plans) > 0:
            plan_types: List[str] = []
            for item in plans:
                payload = safe_json(item)
                plan_types.append(payload.get("type") if payload.get("type") else str(item))
            plan_df = (
                pd.Series(plan_types)
                .value_counts()
                .head(10)
                .rename_axis("plan")
                .reset_index(name="count")
            )
            fig = px.bar(
                plan_df,
                x="count",
                y="plan",
                orientation="h",
                title="Top 10 Proposed Plans",
            )
            fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=360, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    if "customer_type" in cols:
        mix = df["customer_type"].value_counts().rename_axis("Customer Type").reset_index(name="Count")
        mix["Ratio"] = (mix["Count"] / mix["Count"].sum()).round(3)
        st.markdown("### 👥 Customer Mix")
        st.dataframe(mix, use_container_width=True, height=220)


def generate_raw_synthetic(n: int, non_bank_ratio: float) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    names = [
        "Alice Nguyen",
        "Bao Tran",
        "Chris Do",
        "Duy Le",
        "Emma Tran",
        "Felix Nguyen",
        "Giang Ho",
        "Hanh Vo",
        "Ivan Pham",
        "Julia Ngo",
    ]
    emails = [f"{n.split()[0].lower()}.{n.split()[1].lower()}@gmail.com" for n in names]
    addrs = [
        "23 Elm St, Boston, MA",
        "19 Pine Ave, San Jose, CA",
        "14 High St, London, UK",
        "55 Nguyen Hue, Ho Chi Minh",
        "78 Oak St, Chicago, IL",
        "10 Broadway, New York, NY",
        "8 Rue Lafayette, Paris, FR",
        "21 Königstr, Berlin, DE",
        "44 Maple Dr, Los Angeles, CA",
        "22 Bay St, Toronto, CA",
    ]
    is_non = rng.random(n) < non_bank_ratio
    cust_type = np.where(is_non, "non-bank", "bank")

    df = pd.DataFrame(
        {
            "application_id": [f"APP_{i:04d}" for i in range(1, n + 1)],
            "customer_name": np.random.choice(names, n),
            "email": np.random.choice(emails, n),
            "phone": [f"+1-202-555-{1000+i:04d}" for i in range(n)],
            "address": np.random.choice(addrs, n),
            "national_id": rng.integers(10_000_000, 99_999_999, n),
            "age": rng.integers(21, 65, n),
            "income": rng.integers(25_000, 150_000, n),
            "employment_length": rng.integers(0, 30, n),
            "loan_amount": rng.integers(5_000, 100_000, n),
            "loan_duration_months": rng.choice([12, 24, 36, 48, 60, 72], n),
            "collateral_value": rng.integers(8_000, 200_000, n),
            "collateral_type": rng.choice(["real_estate", "car", "land", "deposit"], n),
            "co_loaners": rng.choice([0, 1, 2], n, p=[0.7, 0.25, 0.05]),
            "credit_score": rng.integers(300, 850, n),
            "existing_debt": rng.integers(0, 50_000, n),
            "assets_owned": rng.integers(10_000, 300_000, n),
            "current_loans": rng.integers(0, 5, n),
            "customer_type": cust_type,
        }
    )
    eps = 1e-9
    df["DTI"] = df["existing_debt"] / (df["income"] + eps)
    df["LTV"] = df["loan_amount"] / (df["collateral_value"] + eps)
    df["CCR"] = df["collateral_value"] / (df["loan_amount"] + eps)
    df["ITI"] = (df["loan_amount"] / (df["loan_duration_months"] + eps)) / (df["income"] + eps)
    df["CWI"] = ((1 - df["DTI"]).clip(0, 1)) * ((1 - df["LTV"]).clip(0, 1)) * (df["CCR"].clip(0, 3))

    fx = st.session_state.get("currency_fx", 1.0)
    for col in ("income", "loan_amount", "collateral_value", "assets_owned", "existing_debt"):
        df[col] = (df[col] * fx).round(2)
    df["currency_code"] = st.session_state.get("currency_code", "USD")
    return dedupe_columns(df)


def generate_anon_synthetic(n: int, non_bank_ratio: float) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    is_non = rng.random(n) < non_bank_ratio
    cust_type = np.where(is_non, "non-bank", "bank")

    df = pd.DataFrame(
        {
            "application_id": [f"APP_{i:04d}" for i in range(1, n + 1)],
            "age": rng.integers(21, 65, n),
            "income": rng.integers(25_000, 150_000, n),
            "employment_length": rng.integers(0, 30, n),
            "loan_amount": rng.integers(5_000, 100_000, n),
            "loan_duration_months": rng.choice([12, 24, 36, 48, 60, 72], n),
            "collateral_value": rng.integers(8_000, 200_000, n),
            "collateral_type": rng.choice(["real_estate", "car", "land", "deposit"], n),
            "co_loaners": rng.choice([0, 1, 2], n, p=[0.7, 0.25, 0.05]),
            "credit_score": rng.integers(300, 850, n),
            "existing_debt": rng.integers(0, 50_000, n),
            "assets_owned": rng.integers(10_000, 300_000, n),
            "current_loans": rng.integers(0, 5, n),
            "customer_type": cust_type,
        }
    )
    eps = 1e-9
    df["DTI"] = df["existing_debt"] / (df["income"] + eps)
    df["LTV"] = df["loan_amount"] / (df["collateral_value"] + eps)
    df["CCR"] = df["collateral_value"] / (df["loan_amount"] + eps)
    df["ITI"] = (df["loan_amount"] / (df["loan_duration_months"] + eps)) / (df["income"] + eps)
    df["CWI"] = ((1 - df["DTI"]).clip(0, 1)) * ((1 - df["LTV"]).clip(0, 1)) * (df["CCR"].clip(0, 3))

    fx = st.session_state.get("currency_fx", 1.0)
    for col in ("income", "loan_amount", "collateral_value", "assets_owned", "existing_debt"):
        df[col] = (df[col] * fx).round(2)
    df["currency_code"] = st.session_state.get("currency_code", "USD")
    return dedupe_columns(df)


def to_agent_schema(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    n = len(out)
    if "employment_years" not in out.columns:
        out["employment_years"] = out.get("employment_length", 0)
    if "debt_to_income" not in out.columns:
        if "DTI" in out.columns:
            out["debt_to_income"] = out["DTI"].astype(float)
        elif {"existing_debt", "income"} <= set(out.columns):
            denom = out["income"].replace(0, np.nan)
            dti = (out["existing_debt"] / denom).fillna(0.0)
            out["debt_to_income"] = dti.clip(0, 10)
        else:
            out["debt_to_income"] = 0.0
    rng = np.random.default_rng(12345)
    if "credit_history_length" not in out.columns:
        out["credit_history_length"] = rng.integers(0, 30, n)
    if "num_delinquencies" not in out.columns:
        out["num_delinquencies"] = np.minimum(rng.poisson(0.2, n), 10)
    if "requested_amount" not in out.columns:
        out["requested_amount"] = out.get("loan_amount", 0)
    if "loan_term_months" not in out.columns:
        out["loan_term_months"] = out.get("loan_duration_months", 0)
    return dedupe_columns(out)


def fetch_production_meta(api_url: str) -> Optional[Dict[str, Any]]:
    try:
        resp = requests.get(f"{api_url}/v1/training/production_meta", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None


def build_training_payload(staged_paths: Iterable[str]) -> Dict[str, Any]:
    return {
        "feedback_csvs": list(staged_paths),
        "user_name": st.session_state.get("user_info", {}).get("name", ""),
        "agent_name": "credit_appraisal",
        "algo_name": "credit_lr",
    }

