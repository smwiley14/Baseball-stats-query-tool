#!/usr/bin/env bash
set -euo pipefail

echo "Starting LangGraph server..."
cd "$(dirname "$0")"
langgraph dev --config langgraph.json --host 0.0.0.0 --port 8000
