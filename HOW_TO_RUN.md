# Digital Twin — 啟動與分享指南

## 第一步：啟動系統

**唯一啟動方法：**
```bash
cd /c/Users/kwanw/Desktop/digital-twin-dialectical
.venv/Scripts/python.exe run.py
```

看到 `Uvicorn running on http://0.0.0.0:5678` 就是成功。

**驗證：**
- 打開瀏覽器訪問 `http://127.0.0.1:5678/`
- 見到「Digital Twin · 你的數碼身份代理」落地頁 = 正常

---

## 第二步：自己用

### 本地使用
- 儀表板：`http://127.0.0.1:5678/docs/index.html`
- 辯證模式：`http://127.0.0.1:5678/dashboard/dashboard.html`

### 手機（同一 WiFi）
- 確保電腦和手機在同一 WiFi
- 手機瀏覽器打開：`http://192.168.0.59:5678/docs/index.html`
- 登入帳號即可使用

### 外網分享（給任何人測試）
**方法：Cloudflare Tunnel**
```bash
# 開新視窗，運行：
npx cloudflared tunnel --url http://127.0.0.1:5678
```
複製顯示的 `https://xxxx.trycloudflare.com` 這個 URL 發給任何人即可。

**注意：** 這個 URL 每次重啟都會變。要固定域名需要額外設定。

---

## 第三步：發給客人測試

### 最簡單方法（推薦）
直接把 Cloudflare Tunnel URL 發給對方，例如：
```
https://summit-valley-monsters-genes.trycloudflare.com
```

對方打開後：
1. 點「開啟儀表板」
2. 註冊新帳號
3. 開始體驗

### 同一辦公室/家裡（最简单）
直接發：
```
http://192.168.0.59:5678/
```

---

## 重要提示

### 系統不能關機
分享期間，電腦不能關機或睡眠，否則系統停止。

### 數據安全
- 目前所有數據存在本地 SQLite
- 備份功能：`POST /identity/backup/export` 可匯出 JSON
- 測試完可刪除數據庫重置

### 測試帳號建議
讓客人自己註冊，不要給你的主帳號。

---

## 常見問題

**Q: 別人打不開？**
A: 檢查防火牆是否允許 5678 port，或改用 Cloudflare Tunnel。

**Q: URL 變了？**
A: Cloudflare Tunnel 免費版每次重啟會換 URL，這是正常的。

**Q: 如何停止系統？**
A: 在運行 `run.py` 的視窗按 `Ctrl+C`，或直接關閉終端。

**Q: 如何重置所有數據？**
A: 關閉系統，刪除 `data/` 資料夾內的所有 `.db` 文件，重啟即重置。
