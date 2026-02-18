#!/bin/bash

# Start FastAPI backend server
echo "Starting FastAPI backend server..."
cd "$(dirname "$0")"
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
