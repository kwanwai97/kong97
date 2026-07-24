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
start http://127.0.0.1:5678/dashboard/dashboard.html

echo.
echo Digital Twin is running at http://127.0.0.1:5678/dashboard/dashboard.html
echo Do NOT close this window while using the system.
echo.
pause
