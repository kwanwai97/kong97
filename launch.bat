@echo off
chcp 65001 >nul
cd /d C:\Users\kwanw\Desktop\digital-twin-dialectical

echo killing old 5678...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5678 ^| findstr LISTENING ^| findstr /v /c:"127.0.0.1:5678"') do taskkill //F //PID %%a >nul 2>&1

echo starting backend...
start "DigitalTwin" /B .venv\Scripts\python.exe run.py

ping -n 6 127.0.0.1 >nul
echo http://127.0.0.1:5678/dashboard/dashboard.html
start http://127.0.0.1:5678/dashboard/dashboard.html
ping -n 3 127.0.0.1 >nul
exit
