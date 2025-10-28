#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
# 🧠 AI Sandbox Launcher (Hub + Agents + UI)
# Author: Dzoan (Rackspace FAIR)
# Purpose: Launches all AI agents, the hub, and Streamlit dashboard
# ──────────────────────────────────────────────

ROOT="${ROOT:-$HOME/AiSandbox2}"
HUB_PORT=8090
CREDIT_PORT=8091
ASSET_PORT=8092
UI_PORT=8502
LOGDIR="${ROOT}/.logs"

mkdir -p "$LOGDIR"

echo "🚀 Launching Rackspace AI Sandbox environment..."
echo "📁 Root: $ROOT"
echo "🗂️ Logs: $LOGDIR"
echo "──────────────────────────────────────────────"

# Kill previous runs
pkill -f "uvicorn.*${HUB_PORT}" || true
pkill -f "uvicorn.*${CREDIT_PORT}" || true
pkill -f "uvicorn.*${ASSET_PORT}" || true
pkill -f "streamlit.*${UI_PORT}" || true

# ── Launch Credit Agent ───────────────────────────────
if [ -d "${ROOT}/agent-credit-appraisal" ]; then
  echo "💳 Starting Credit Appraisal Agent on port ${CREDIT_PORT}..."
  (cd "${ROOT}/agent-credit-appraisal" && \
   if [ -f requirements.txt ]; then pip install -q -r requirements.txt; fi && \
   nohup uvicorn main:app --port ${CREDIT_PORT} --reload > "${LOGDIR}/credit.log" 2>&1 &)
else
  echo "⚠️  Credit agent folder not found at ${ROOT}/agent-credit-appraisal"
fi

# ── Launch Asset Agent ───────────────────────────────
if [ -d "${ROOT}/agent-asset-appraisal" ]; then
  echo "🏛️ Starting Asset Appraisal Agent on port ${ASSET_PORT}..."
  (cd "${ROOT}/agent-asset-appraisal" && \
   if [ -f requirements.txt ]; then pip install -q -r requirements.txt; fi && \
   nohup uvicorn main:app --port ${ASSET_PORT} --reload > "${LOGDIR}/asset.log" 2>&1 &)
else
  echo "⚠️  Asset agent folder not found at ${ROOT}/agent-asset-appraisal"
fi

# ── Launch AI Hub ───────────────────────────────
if [ -d "${ROOT}/ai-agent-hub" ]; then
  echo "🧠 Starting AI Agent Hub on port ${HUB_PORT}..."
  (cd "${ROOT}/ai-agent-hub" && \
   if [ -f requirements.txt ]; then pip install -q -r requirements.txt; fi && \
   nohup uvicorn services.api.main:app --port ${HUB_PORT} --reload > "${LOGDIR}/hub.log" 2>&1 &)
else
  echo "⚠️  AI Agent Hub not found at ${ROOT}/ai-agent-hub"
fi

# ── Launch Streamlit UI ───────────────────────────────
UI_PATH="${ROOT}/ai-agent-hub/services/ui"
if [ -d "$UI_PATH" ]; then
  echo "🖥️  Launching Streamlit Dashboard on port ${UI_PORT}..."
  (cd "$UI_PATH" && \
   if [ -f requirements.txt ]; then pip install -q -r requirements.txt; fi && \
   nohup streamlit run app.py --server.port ${UI_PORT} > "${LOGDIR}/ui.log" 2>&1 &)
else
  echo "⚠️  Streamlit UI folder not found at ${UI_PATH}"
fi

# ──────────────────────────────────────────────
#  Health Check
# ──────────────────────────────────────────────
sleep 6
echo "──────────────────────────────────────────────"
echo "🌐 Checking health endpoints..."
for url in \
  "http://localhost:${HUB_PORT}/health" \
  "http://localhost:${CREDIT_PORT}/health" \
  "http://localhost:${ASSET_PORT}/health"
do
  echo -n "   → $url : "
  curl -s "$url" || echo "❌ not reachable"
  echo
done

echo "──────────────────────────────────────────────"
echo "✅ All services launched successfully!"
echo "   🧠 Hub:     http://localhost:${HUB_PORT}"
echo "   💳 Credit:  http://localhost:${CREDIT_PORT}"
echo "   🏛️ Asset:   http://localhost:${ASSET_PORT}"
echo "   🖥️  UI:      http://localhost:${UI_PORT}"
echo "──────────────────────────────────────────────"
echo "🧾 Logs → tail -f ${LOGDIR}/*.log"
