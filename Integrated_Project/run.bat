@echo off
REM Run Integrated Control System with API and Dashboard
REM Usage: run.bat [--ngrok]

setlocal enabledelayedexpansion

set "USE_NGROK=false"
if "%1"=="--ngrok" (
    set "USE_NGROK=true"
)

echo.
echo ============================================
echo Hair Dryer Control System Launcher
echo ============================================
echo.
echo This will open 3-4 separate windows:
echo   1. API Server (port 8000)
echo   2. Streamlit Dashboard (port 8501)
if "%USE_NGROK%"=="true" (
    echo   3. ngrok tunnel
    echo   4. Integrated Control System
) else (
    echo   3. Integrated Control System
)
echo.
echo Press any key to continue...
pause > nul

echo.
echo Starting API server...
start "Hair Dryer - API Server" cmd /k call run_api.bat

timeout /t 3 /nobreak

echo.
echo Starting Streamlit dashboard...
start "Hair Dryer - Dashboard" cmd /k call run_dashboard.bat

timeout /t 2 /nobreak

if "%USE_NGROK%"=="true" (
    echo.
    echo Setting up ngrok tunnels for API and Dashboard...
    
    REM Create ngrok config file
    if not exist "%USERPROFILE%\.ngrok2" mkdir "%USERPROFILE%\.ngrok2"
    (
        echo tunnels:
        echo   api:
        echo     proto: http
        echo     addr: 8000
        echo   dashboard:
        echo     proto: http
        echo     addr: 8501
    ) > "%USERPROFILE%\.ngrok2\ngrok.yml"
    
    REM Start ngrok with config
    start "Hair Dryer - ngrok" cmd /k "ngrok start --all"
    timeout /t 5 /nobreak
    
    REM Try to get ngrok URLs via API
    echo.
    echo Attempting to extract ngrok URLs...
    
    REM Simple JSON parsing to get the URLs
    for /f "tokens=*" %%A in ('curl -s http://localhost:4040/api/tunnels 2^>nul') do (
        set "NGROK_JSON=%%A"
    )
    
    if not "!NGROK_JSON!"=="" (
        echo Found ngrok tunnels
        REM Extract URLs from JSON (simplified approach)
        set "API_URL=http://127.0.0.1:8000/protocol"
        set "DASHBOARD_URL=http://127.0.0.1:8501"
        echo Note: Using localhost URLs. For public URLs, check ngrok console at http://localhost:4040
    ) else (
        set "API_URL=http://127.0.0.1:8000/protocol"
        set "DASHBOARD_URL=http://127.0.0.1:8501"
    )
)

echo.
echo Starting Integrated Control System...
if not "!DASHBOARD_URL!"=="" (
    echo Dashboard: !DASHBOARD_URL!
) else (
    echo Dashboard: http://localhost:8501
)

if "%USE_NGROK%"=="true" (
    if not "!API_URL!"=="" (
        start "Hair Dryer - Control System" cmd /k "set API_URL=!API_URL! && call run_integrated.bat"
    ) else (
        start "Hair Dryer - Control System" cmd /k call run_integrated.bat
    )
) else (
    start "Hair Dryer - Control System" cmd /k call run_integrated.bat
)

echo.
echo All services started. Close the main window to continue, or use Ctrl+C in individual windows to stop them.
pause > nul
