# Next-Gen AI Digital Twin：辯證合夥人架構

本檔案為《新世代 AI 數位孿生（辯證合夥人版）》之系統骨架與快速啟動指南。

## 核心設計

- 辯格拉底式反向質疑（Antagonistic Thinking）
- 跨領域融合對撞（Cross-Domain Synthesis）
- 夜間自主探索（Autonomous Exploration）
- 人機協同限制（Human-in-the-Loop）

## 快速啟動

```bash
git clone <your-repo-url>
cd digital-twin-dialectical
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python run.py
```

## 驗證

```bash
curl http://127.0.0.1:5678/health
```

## 部署

### Railway
1. 註冊 Railway：https://railway.app
2. 安裝 CLI：`npm i -g @railway/cli`
3. 登入：`railway login`
4. 初始化：`railway init --name digital-twin`
5. 部署：`railway up`

### Render / Fly.io
- 連接 GitHub repo
- Build Command：`pip install -r requirements.txt`
- Start Command：`python run.py`
- Port：`5678`
- 建議加上環境變數：`OPENAI_API_KEY`

## 系統結構

```
digital-twin-dialectical/
├── README.md
├── requirements.txt
├── .env.example
├── run.py
├── DEPLOY.md
├── docs/
├── backend/
│   ├── api/main.py
│   ├── brain/{thesis,antithesis,synthesis,memory_graph}.py
│   ├── explorer/{night_wanderer,peer_alignment,briefing,arxiv,github,hackernews}.py
│   └── safety/human_in_the_loop.py
├── frontend/app/components/dashboard.html
├── tests/
└── data/
```

## 功能 API

- `GET /health`
- `GET /`
- `POST /ingest`
- `POST /dialectic`
- `GET /digest`
- `GET /briefing/today`
- `POST /schedule/briefing`
- `GET /memory/search?q=`
- `POST /peers/align`
- `POST /approve`

## Roadmap

- 第一階段：基礎骨架與前端入口
- 第二階段：辯證引擎記憶強化
- 第三階段：夜間巡邏 + 簡報
- 第四階段：前端情報面板與自動巡覽
