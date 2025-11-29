#!/bin/bash

# Hair Dryer Assistant - Full Stack Launcher (api/ structure)
echo "🚀 Starting API server (port 8000) from api/..."
# Start FastAPI from api/ directory
cd "$(dirname "$0")/api"
uvicorn mock_protocol_api:app --host 127.0.0.1 --port 8000 --reload &
API_PID=$!
sleep 3  # Wait for API startup

echo "📱 Starting Streamlit (port 8501)..."
cd "$(dirname "$0")"
streamlit run StreamlitDashboard.py --server.headless=true --server.port=8501 &

echo "✅ Full stack running!"
echo "🌐 API: http://127.0.0.1:8000/protocol"
echo "📱 Dashboard: http://localhost:8501" 
echo "🛑 Press Ctrl+C to stop everything"

# Cleanup on exit
trap "kill $API_PID 2>/dev/null; exit" INT TERM
wait
