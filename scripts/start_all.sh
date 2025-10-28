#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
# 🧠 AI Sandbox Launcher (Hub + Agents)
# Author: Dzoan (Rackspace FAIR)
# ──────────────────────────────────────────────

ROOT="${ROOT:-$HOME/AiSandbox2}"
HUB_PORT=8090
CREDIT_PORT=8091
ASSET_PORT=8092
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

# ── Launch Credit Agent ───────────────────────────────
if [ -d "${ROOT}/agent-credit-appraisal" ]; then
  echo "💳 Starting Credit Appraisal Agent on port ${CREDIT_PORT}..."
  (cd "${ROOT}/agent-credit-appraisal" && \
   pip install -q -r requirements.txt && \
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
   pip install -q -r requirements.txt && \
   nohup uvicorn services.api.main:app --port ${HUB_PORT} --reload > "${LOGDIR}/hub.log" 2>&1 &)
else
  echo "⚠️  AI Agent Hub not found at ${ROOT}/ai-agent-hub"
fi

sleep 5
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
echo "✅ All services launched (hub:${HUB_PORT}, credit:${CREDIT_PORT}, asset:${ASSET_PORT})"
echo "🧾 Logs: tail -f ${LOGDIR}/*.log"
