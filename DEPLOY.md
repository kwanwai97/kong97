# Deploy Guide

## 1) GitHub Pages（免費 HTTPS，永久）
1. 打開 repo：https://github.com/kwanwai97/kong97/settings/pages
2. Source 選擇 `Deploy from a branch`
3. Branch 選擇 `main`，資料夾選 `/docs`
4. Save。等約 1-2 分鐘，網站會出現在：
   - `https://kwanwai97.github.io/kong97/`
5. 進入頁面後，在「後端 Base URL」輸入你的後端 HTTPS 網址並按「儲存」

## 2) 後端部署（任選其一）
- Railway：https://railway.app → New Project → Deploy from GitHub → 選擇 `kwanwai97/kong97`
  ⚠️ Railway 免費 tier 需要綁定信用卡
- Fly.io：https://fly.io → `fly launch` → `fly deploy`
- Render：https://render.com → New Web Service → connect repo

如果不想付費，後端可繼續在本機用 `launch.bat` 啟動，frontend 的 GitHub Pages 一樣可以用。

## 注意
- 後端必須是你可連線的 HTTPS/HTTP 位址，不能是 `127.0.0.1`
- 前端 base URL 存在瀏覽器 localStorage，一次設定就會記住
