# Deploy Guide

## 1) Railway（推薦，5 分鐘）
1. 註冊 Railway：https://railway.app
2. 安裝 CLI：
   ```powershell
   npm i -g @railway/cli
   railway login
   ```
3. 初始化並部署：
   ```powershell
   cd C:\Users\wai\Desktop\digital-twin-dialectical
   railway init --name digital-twin
   railway up
   ```
4. 完成後 Railway 會給你一個公開 URL，例如：
   `https://<project>.up.railway.app`

## 2) Render（免費 tier）
1. 註冊 Render：https://render.com
2. 連接你的 GitHub repo：`kwanwai97/kong97`
3. 建立 Web Service：
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run.py`
   - Port: `5678`

## 3) Fly.io
1. 註冊 Fly：https://fly.io
2. 安裝 CLI：
   ```powershell
   pwsh -Command "iwr https://fly.io/install.ps1 -UseBasicParsing | iex"
   ```
3. 部署：
   ```powershell
   cd C:\Users\wai\Desktop\digital-twin-dialectical
   fly launch
   fly deploy
   ```

## 注意
- OpenAI API Key 需要在部署平台上設定環境變數 `OPENAI_API_KEY`，否則會自動 fallback 到 mock 模式。
- 如果不需要真實 AI，系統仍可正常運行。
