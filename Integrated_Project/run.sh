#!/bin/bash
# Run Integrated Control System with API and Dashboard
# Uses tmux to run each service in its own session
# Usage: ./run.sh [--ngrok]

SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR"

USE_NGROK=false
if [[ "$1" == "--ngrok" ]]; then
    USE_NGROK=true
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo -e "${YELLOW}tmux not found. Install with: brew install tmux${NC}"
    echo "Falling back to background processes..."
    # Run without tmux
    bash run_api.sh > api.log 2>&1 &
    sleep 3
    bash run_dashboard.sh > dashboard.log 2>&1 &
    sleep 3
    export API_URL="http://127.0.0.1:8000/protocol"
    bash run_integrated.sh
    exit
fi

# Kill any existing session
tmux kill-session -t "hair-dryer" 2>/dev/null || true

# Create new tmux session with multiple windows
tmux new-session -d -s "hair-dryer" -x 250 -y 50

# Window 0: API Server
echo -e "${GREEN}[1/3] Starting API server${NC}"
tmux send-keys -t "hair-dryer:0" "cd '$SCRIPT_DIR' && bash run_api.sh" Enter
sleep 3

# Window 1: Dashboard
echo -e "${GREEN}[2/3] Starting Streamlit dashboard${NC}"
tmux new-window -t "hair-dryer:1"
tmux send-keys -t "hair-dryer:1" "cd '$SCRIPT_DIR' && bash run_dashboard.sh" Enter
sleep 2

# Window 2: Integrated Control System
echo -e "${GREEN}[3/3] Starting Integrated Control System${NC}"
tmux new-window -t "hair-dryer:2"

if [[ "$USE_NGROK" == true ]]; then
    echo -e "${BLUE}Setting up ngrok tunnels for both API and Dashboard...${NC}"
    
    # Create ngrok config file
    mkdir -p ~/.ngrok2
    cat > ~/.ngrok2/ngrok.yml <<'NGROK_CONFIG'
tunnels:
  api:
    proto: http
    addr: 8000
  dashboard:
    proto: http
    addr: 8501
NGROK_CONFIG
    
    # Start ngrok with config file
    tmux send-keys -t "hair-dryer:2" "ngrok start --all" Enter
    sleep 5
    
    # Get ngrok URLs from API
    API_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[a-z0-9-]*\.ngrok\.io' | head -1 | cut -d'"' -f4)
    DASHBOARD_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[a-z0-9-]*\.ngrok\.io' | tail -1 | cut -d'"' -f4)
    
    if [ ! -z "$API_URL" ] && [ ! -z "$DASHBOARD_URL" ]; then
        API_URL="${API_URL}/protocol"
        export API_URL
        export DASHBOARD_URL
        echo -e "${GREEN}API URL: ${API_URL}${NC}"
        echo -e "${GREEN}Dashboard URL: ${DASHBOARD_URL}${NC}"
    else
        echo -e "${YELLOW}Could not get ngrok URLs, using localhost${NC}"
        export API_URL="http://127.0.0.1:8000/protocol"
        export DASHBOARD_URL="http://127.0.0.1:8501"
    fi
else
    export API_URL="http://127.0.0.1:8000/protocol"
    export DASHBOARD_URL="http://127.0.0.1:8501"
fi

# Create a new window for the integrated system
tmux new-window -t "hair-dryer:3"
tmux send-keys -t "hair-dryer:3" "cd '$SCRIPT_DIR' && export API_URL='${API_URL}' && bash run_integrated.sh" Enter

echo ""
echo -e "${GREEN}Services started in tmux session 'hair-dryer'${NC}"
echo ""
echo "📊 Starting Integrated Control System"
if [ ! -z "$DASHBOARD_URL" ] && [ "$DASHBOARD_URL" != "http://127.0.0.1:8501" ]; then
    echo -e "${GREEN}Dashboard: ${DASHBOARD_URL}${NC}"
else
    echo "Dashboard: http://localhost:8501"
fi
echo ""
echo "Commands:"
echo "  tmux attach -t hair-dryer        # Attach to session"
echo "  tmux list-windows -t hair-dryer  # List windows"
echo ""
echo "Windows:"
echo "  0: API Server (http://localhost:8000)"
echo "  1: Dashboard (http://localhost:8501)"
echo "  2: ngrok tunnel (if using --ngrok)"
echo "  3: Integrated Control System"
echo ""
echo "To kill all services: tmux kill-session -t hair-dryer"
echo ""

# Attach to session
tmux attach -t "hair-dryer"
