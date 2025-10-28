#!/usr/bin/env bash
set -euo pipefail

echo "🛑 Stopping all AI Sandbox services..."
pkill -f "uvicorn.*8090" || true
pkill -f "uvicorn.*8091" || true
pkill -f "uvicorn.*8092" || true
echo "✅ All stopped."
