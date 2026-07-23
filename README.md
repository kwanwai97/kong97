# Next-Gen AI Digital Twin: 辯證合夥人架構

新世代 AI 數位孿生（辯證合夥人版）的系統骨架與快速啟動指南。

## 願景

打破傳統代理侷限，強制要求：
- 辯格拉底式反向質疑（Antagonistic Thinking）
- 跨領域融合對撞（Cross-Domain Synthesis）
- 夜間自主探索（Autonomous Exploration）
- 人機權限控制（Human-in-the-Loop）

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

## End-to-end 驗證

```bash
curl http://127.0.0.1:5678/health
```

## 部署到雲端

### Railway
1. 安裝 Railway CLI
2. `railway init`
3. `railway up`

### Render / Fly.io
- 連接 GitHub repo
- Build Command: `pip install -r requirements.txt`
- Start Command: `python run.py`
- Port: `5678`

## 系統結構

```
digital-twin-dialectical/
├── README.md
├── requirements.txt
├── .env.example
├── run.py
├── docs/QUICKSTART.md
├── backend/
│   ├── api/main.py
│   ├── brain/{thesis,antithesis,synthesis,memory_graph}.py
│   ├── explorer/{night_wanderer,peer_alignment,briefing}.py
│   └── safety/human_in_the_loop.py
├── frontend/app/components/dashboard.html
└── data/memory_graph.json
```

## Endpoints

- `GET /health`
- `GET /`
- `POST /ingest`
- `POST /dialectic`
- `GET /digest`
- `GET /memory/search?q=`
- `POST /peers/align`
- `POST /approve`

## Roadmap

- Phase 1：基礎骨架與前端入口
- Phase 2：辯證引擎記憶強化
- Phase 3：夜間巡邏 + briefing
- Phase 4：Dashboard 豐富化
