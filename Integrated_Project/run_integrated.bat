@echo off
REM Run Integrated Control System only

setlocal enabledelayedexpansion

if "%API_URL%"=="" (
    set "API_URL=http://127.0.0.1:8000/protocol"
)

if "%DASHBOARD_URL%"=="" (
    set "DASHBOARD_URL=http://127.0.0.1:8501"
)

echo Starting Integrated Control System
echo Dashboard: %DASHBOARD_URL%
echo Using API_URL: %API_URL%
python -m pip install -q pyserial requests 2>nul

python Integrated_Project.py COM7
pause
