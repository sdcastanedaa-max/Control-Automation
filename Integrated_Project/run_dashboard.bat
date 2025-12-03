@echo off
REM Run Streamlit dashboard only

setlocal enabledelayedexpansion

if "%API_URL%"=="" (
    set "API_URL=http://127.0.0.1:8000/protocol"
)

echo Starting Streamlit dashboard on http://localhost:8501
echo Using API_URL: %API_URL%
python -m pip install -q streamlit plotly numpy requests 2>nul

set "API_URL=%API_URL%"
streamlit run StreamlitDashboard.py --logger.level=warning
pause
