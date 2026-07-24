@echo off
chcp 65001 >nul
cd /d C:\Users\kwanw\Desktop\digital-twin-dialectical

echo killing old 5678...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5678 ^| findstr LISTENING ^| findstr /v /c:"127.0.0.1:5678"') do taskkill //F //PID %%a >nul 2>&1

echo starting backend...
start "DigitalTwin Backend" /B .venv\Scripts\python.exe run.py

echo waiting backend...
:wait
timeout /t 1 /nobreak >nul
curl -s http://127.0.0.1:5678/health >nul 2>&1
if errorlevel 1 goto wait

echo backend is up.

:: Detect LAN IP for mobile access
for /f "tokens=2 delims=:" %%I in ('ipconfig ^| findstr /i "IPv4"') do (
  set "LANIP=%%I"
  goto :gotip
)
:gotip
set "LANIP=%LANIP: =%"

echo.
echo ============================================================
echo Digital Twin is running:
echo   - This PC: http://127.0.0.1:5678/dashboard/dashboard.html
echo   - Mobile:   http://%LANIP%:5678/dashboard/dashboard.html
echo.
echo If your phone cannot connect:
echo   1) Make sure your phone is on the same Wi-Fi as this PC.
echo   2) If still blocked, allow port 5678 through Windows Firewall.
echo ============================================================
echo.

start http://127.0.0.1:5678/dashboard/dashboard.html
echo Do NOT close this window while using the system.
pause
