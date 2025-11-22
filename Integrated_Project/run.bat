@echo off
echo ============================================
echo Integrated Project Launcher
echo ============================================
echo.
echo STEP 1: Upload Integrated_Project.ino to ESP32
echo         (Use Arduino IDE or PlatformIO)
echo.
echo STEP 2: Press any key to run Python script...
pause > nul
echo.
echo Starting Python control interface...
echo.
python Integrated_Project.py
