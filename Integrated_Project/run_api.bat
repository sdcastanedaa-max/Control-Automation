@echo off
REM Run API server only

setlocal enabledelayedexpansion

set "HOST=0.0.0.0"
set "PORT=8000"

echo Starting API server on http://0.0.0.0:8000
python -m pip install -q fastapi uvicorn pydantic requests 2>nul

python api/mock_protocol_api.py
pause
