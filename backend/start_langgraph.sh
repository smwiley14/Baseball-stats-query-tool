#!/usr/bin/env bash
set -euo pipefail

echo "Starting LangGraph server..."
cd "$(dirname "$0")"
# Port 2024 (LangGraph's own default), not 8000 — that's the Docker backend's port.
langgraph dev --config langgraph.json --host 0.0.0.0 --port 2024
