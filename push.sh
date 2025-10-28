#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
# 🧠 Git Push Automation Script
# Author: Dzoan (Rackspace FAIR)
# Purpose: Sync local AI Sandbox to remote GitHub repo
# ──────────────────────────────────────────────

REPO_DIR="${HOME}/AiSandbox2"
REMOTE_URL="git@github.com:Sherlock2019/Aisandboxlibrary.git"
BRANCH="main"
COMMIT_MSG="${1:-Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')}"

echo "🚀 Preparing to push AI Sandbox to GitHub"
echo "📂 Directory: ${REPO_DIR}"
echo "🌍 Remote: ${REMOTE_URL}"
echo "──────────────────────────────────────────────"

cd "${REPO_DIR}"

# Initialize git repo if not already
if [ ! -d .git ]; then
  echo "📦 Initializing new git repository..."
  git init
  git branch -M ${BRANCH}
fi

# Ensure remote is set
if git remote get-url origin &>/dev/null; then
  echo "🔗 Remote 'origin' already set."
else
  echo "🔗 Adding remote origin..."
  git remote add origin "${REMOTE_URL}"
fi

# Add all files and commit
echo "📸 Staging changes..."
git add -A

if git diff --cached --quiet; then
  echo "✅ No changes to commit."
else
  echo "📝 Committing changes..."
  git commit -m "${COMMIT_MSG}" || echo "⚠️  Nothing new to commit."
fi

# Pull + merge before pushing (safe sync)
echo "🔄 Syncing with remote..."
git fetch origin ${BRANCH} || true
git pull origin ${BRANCH} --rebase || true

# Push changes
echo "🚀 Pushing to ${REMOTE_URL} ..."
git push -u origin ${BRANCH}

echo "✅ Repository successfully pushed!"
