#!/bin/bash
# Run API server only

cd "$(dirname "$0")"
export HOST="0.0.0.0"
export PORT=8000

echo "Starting API server on http://0.0.0.0:8000"
/opt/anaconda3/bin/python -m pip install -q fastapi uvicorn pydantic requests 2>/dev/null || true
/opt/anaconda3/bin/python api/mock_protocol_api.py
