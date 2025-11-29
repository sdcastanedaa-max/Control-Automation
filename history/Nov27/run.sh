#!/bin/bash

# Hair Dryer Assistant Streamlit App Runner
# This script starts the Streamlit app with optimal settings

# Create Streamlit config directory if it doesn't exist
mkdir -p ~/.streamlit

# Create config file to disable telemetry
cat > ~/.streamlit/config.toml << 'EOF'
[browser]
gatherUsageStats = false

[client]
toolbarMode = "minimal"

[server]
headless = true
EOF

echo "🚀 Starting Hair Dryer Assistant..."
echo "📱 Access the app at: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Run Streamlit app
streamlit run StreamlitDashboard.py --server.headless=true
