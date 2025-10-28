#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
# 🧠 fix_agents.sh — Quick-fix for empty agent repos
# Author: Dzoan (Rackspace FAIR)
# Purpose: Creates working FastAPI apps for Credit + Asset agents
# ──────────────────────────────────────────────

ROOT="${ROOT:-$HOME/AiSandbox2}"
CREDIT_DIR="${ROOT}/agent-credit-appraisal"
ASSET_DIR="${ROOT}/agent-asset-appraisal"

echo "🔧 Repairing agent folders under $ROOT"

# ──────────────────────────────────────────────
# 💳 Credit Appraisal Agent
# ──────────────────────────────────────────────
mkdir -p "$CREDIT_DIR"

cat > "${CREDIT_DIR}/main.py" <<'EOF'
from fastapi import FastAPI

app = FastAPI(title="Credit Appraisal Agent")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run")
def run(payload: dict):
    text = payload.get("text", "")
    decision = "approve" if "income" in text.lower() or "stable" in text.lower() else "review"
    return {"decision": decision, "confidence": 0.87}
EOF

cat > "${CREDIT_DIR}/requirements.txt" <<'EOF'
fastapi
uvicorn
EOF

echo "✅ Credit Appraisal Agent fixed at ${CREDIT_DIR}"

# ──────────────────────────────────────────────
# 🏛️ Asset Appraisal Agent
# ──────────────────────────────────────────────
mkdir -p "$ASSET_DIR"

cat > "${ASSET_DIR}/main.py" <<'EOF'
from fastapi import FastAPI

app = FastAPI(title="Asset Appraisal Agent")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run")
def run(payload: dict):
    asset = payload.get("asset", "property")
    base_value = 100000
    adjustment = 1.1 if "villa" in asset.lower() else 0.9 if "land" in asset.lower() else 1.0
    est_value = base_value * adjustment
    confidence = 0.9
    return {"estimated_value": est_value, "confidence": confidence}
EOF

cat > "${ASSET_DIR}/requirements.txt" <<'EOF'
fastapi
uvicorn
EOF

echo "✅ Asset Appraisal Agent fixed at ${ASSET_DIR}"

# ──────────────────────────────────────────────
# 🚀 Restart everything
# ──────────────────────────────────────────────
echo "♻️  Restarting AI Sandbox ..."
bash "${ROOT}/scripts/stop_all.sh" || true
bash "${ROOT}/scripts/start_all.sh"

echo "✅ All agents fixed and sandbox restarted successfully."
