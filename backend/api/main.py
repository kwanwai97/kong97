"""
系統對外入口
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.brain.thesis import ThesisEngine
from backend.brain.antithesis import antithesis
from backend.brain.synthesis import synthesis
from backend.brain.memory_graph import MemoryGraph
from backend.explorer.night_wanderer import NightWanderer
from backend.explorer.peer_alignment import PeerAlignment
from backend.explorer.briefing import build_briefing
from backend.explorer.translator import translate_item, translate_briefing
from backend.safety.human_in_the_loop import HumanInTheLoop

app = FastAPI(title="Digital Twin API")

@app.middleware("http")
async def add_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/dashboard"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response

正反合 = ThesisEngine()
記憶體 = MemoryGraph()
巡邏者 = NightWanderer()
對齊器 = PeerAlignment()
協同器 = HumanInTheLoop()

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend" / "app" / "components"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/dashboard", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="dashboard")


class 訊息(BaseModel):
    text: str


class 行動(BaseModel):
    label: str


class 比較(BaseModel):
    a: str
    b: str


@app.get("/health")
def 健康檢查() -> Dict[str, str]:
    return {"狀態": "正常"}


@app.get("/")
def 首頁() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/dashboard.html")


@app.get("/favicon.ico")
def 圖示() -> FileResponse:
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"), status_code=204)


@app.post("/ingest")
def 存入記憶(訊息_: 訊息) -> Dict[str, Any]:
    t = 正反合.ingest(訊息_.text)
    return {"已儲存": True, "思考id": getattr(t, "TS", None)}


@app.post("/dialectic")
def 辯證(訊息_: 訊息) -> Dict[str, Any]:
    正反合.ingest(訊息_.text)
    正, 主題 = 正反合.answer(訊息_.text)
    反 = antithesis.challenge(正, topic=主題)
    整合 = synthesis.fuse(正, 反, topic=主題)
    return {"正方": 正, "反方": 反, "整合結論": 整合}


@app.get("/digest")
def 摘要() -> Dict[str, Any]:
    原始 = 巡邏者.crawl(["arxiv", "github", "hackernews"])
    項目 = [translate_item(it) for it in 原始]
    result = {
        "情報": 項目,
        "摘要": 巡邏者.summarize(項目),
        "已翻譯": True,
    }
    return result


@app.get("/briefing/today")
def 今日簡報() -> Dict[str, Any]:
    日期 = datetime.utcnow().strftime("%Y%m%d")
    路徑 = DATA_DIR / f"briefing_{日期}.json"
    if 路徑.exists():
        try:
            data = json.loads(路徑.read_text(encoding="utf-8"))
            items = data.get("項目", data.get("items", []))
            if isinstance(items, list) and items and not items[0].get("translated"):
                路徑.unlink(missing_ok=True)
            else:
                return data
        except Exception:
            pass
    資料 = build_briefing(translate=True)
    路徑.write_text(json.dumps(資料, ensure_ascii=False, indent=2), encoding="utf-8")
    return 資料


@app.post("/schedule/briefing")
def 手動簡報() -> Dict[str, Any]:
    路徑 = DATA_DIR / "briefing_latest.json"
    資料 = build_briefing()
    路徑.write_text(json.dumps(資料, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"已儲存": True, "路徑": str(路徑), "項目數量": len(資料.get("items", []))}


@app.get("/memory/search")
def 搜尋記憶(查詢: str) -> Dict[str, Any]:
    結果 = 記憶體.search(查詢)
    return {"查詢": 查詢, "結果": 結果, "數量": len(結果)}


@app.post("/peers/align")
def 對齊(資料: 比較) -> Dict[str, Any]:
    結果 = 對齊器.compare(資料.a, 資料.b)
    return {"對齊結果": 結果}


@app.post("/approve")
def 核准(行動_: 行動) -> Dict[str, Any]:
    return {"核准結果": 協同器.approve({"標籤": 行動_.label})}
