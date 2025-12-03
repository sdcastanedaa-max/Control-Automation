#!/bin/bash
# Run Integrated Control System only

cd "$(dirname "$0")"
export API_URL="${API_URL:-http://127.0.0.1:8000/protocol}"
export DASHBOARD_URL="${DASHBOARD_URL:-http://127.0.0.1:8501}"

echo "Starting Integrated Control System"
echo "Dashboard: $DASHBOARD_URL"
echo "Using API_URL: $API_URL"
/opt/anaconda3/bin/python -m pip install -q pyserial requests 2>/dev/null || true
/opt/anaconda3/bin/python Integrated_Project.py
