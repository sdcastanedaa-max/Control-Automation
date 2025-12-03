#!/bin/bash
# Run Streamlit dashboard only

cd "$(dirname "$0")"

# Use public API URL if available, otherwise default to localhost
API_URL="${API_URL:-http://127.0.0.1:8000/protocol}"

echo "Starting Streamlit dashboard on http://localhost:8501"
echo "Using API_URL: $API_URL"
/opt/anaconda3/bin/python -m pip install -q streamlit plotly numpy requests 2>/dev/null || true
export API_URL
/opt/anaconda3/bin/streamlit run StreamlitDashboard.py --logger.level=warning
