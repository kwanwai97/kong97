@echo off
chcp 65001 >nul
echo 正在啟動 Digital Twin 辯證合夥人...
cd /d "%~dp0digital-twin-dialectical"
start "" /B ".venv\Scripts\python.exe" run.py
timeout /t 2 >nul
start http://127.0.0.1:5678/
echo 已啟動，瀏覽器應該會自動打開。
