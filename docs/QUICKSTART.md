# Digital Twin · 啟動方式

1. 建立虛擬環境
2. 安裝依賴
3. 啟動服務
4. 開啟瀏覽器

## Windows（PowerShell / 路徑請照你的位置調整）
```powershell
cd C:\Users\wai\Desktop\digital-twin-dialectical
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

## 常駐背景啟動
```powershell
Start-Process powershell -ArgumentList '-NoExit','python','C:\Users\wai\Desktop\digital-twin-dialectical\run.py'
```

## 定時任務：每日凌晨生成 briefing
編輯後啟動 (`python .scripts\daily_briefing.py`)，或排程执行。
輸出將寫入 `data\briefing_<YYYYMMDD>.json`。

# Digital Twin · 快速啟動

1. 建立 venv
2. `pip install -r requirements.txt`
3. `python run.py`
4. 開啟 `http://127.0.0.1:5678/`
