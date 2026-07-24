"""
系統對外入口
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.brain.thesis import ThesisEngine, _default_thesis, _default_antithesis, _default_synthesis
from backend.brain.antithesis import antithesis
from backend.brain.synthesis import synthesis
from backend.brain.memory_graph import MemoryGraph
from backend.brain.session_aware_memory import SessionMemory
from backend.explorer.night_wanderer import NightWanderer
from backend.explorer.finance import FinancialFetcher
from backend.explorer.peer_alignment import PeerAlignment
from backend.explorer.briefing import build_briefing
from backend.explorer.translator import translate_item, translate_briefing
from backend.safety.human_in_the_loop import HumanInTheLoop

HITL = HumanInTheLoop()

app = FastAPI(title="Digital Twin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/dashboard"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response

正反合 = ThesisEngine()
記憶體 = MemoryGraph()
會話記憶 = SessionMemory()
巡邏者 = NightWanderer()
對齊器 = PeerAlignment()
協同器 = HITL
財經fetcher = FinancialFetcher()

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


@app.get("/brain/status")
def 大腦狀態() -> Dict[str, Any]:
    engine = 正反合
    llm = getattr(engine, "llm", None)
    host = getattr(llm, "base_url", "") if llm else ""
    model = getattr(llm, "model", "") if llm else ""
    key = getattr(llm, "openai_api_key", "") if llm else ""
    provider = "openai" if key else "ollama" if model else "none"
    checks = {
        "model_loaded": bool(model),
        "openai_key_loaded": bool(key),
        "base_url": host,
        "provider": provider,
    }
    # 真實驗證 LLM 可否連線
    ok = False
    latency_ms = 0
    try:
        import time as _time
        t0 = _time.time()
        probe = asyncio.run(正反合.answer("你好，請回覆『連接成功』四個字。", context=""))
        latency_ms = int((_time.time() - t0) * 1000)
        txt = (probe[0] or "").strip()
        ok = len(txt) > 0
        checks.setdefault("probe_prompt", "你好，請回覆『連接成功』四個字。")
        checks.setdefault("probe_reply", txt[:120])
    except Exception as e:
        checks.setdefault("probe_error", str(e)[:200])
        ok = False
        provider = provider + "_probe_failed"
    checks["可用"] = ok
    checks["延遲"] = latency_ms
    if not ok:
        provider = "none"
    return {
        "llm_host": host,
        "llm_model": model,
        "已啟動": ok,
        "provider": provider,
        "openai_key_loaded": bool(key),
        "checks": checks,
    }

@app.get("/")
def 首頁() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/dashboard.html")


@app.get("/favicon.ico")
def 圖示() -> FileResponse:
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"), status_code=204)


@app.post("/ingest")
def 存入記憶(訊息_: 訊息) -> Dict[str, Any]:
    正反合.ingest(訊息_.text)
    return {"已儲存": True}


@app.post("/dialectic")
def 辯證(訊息_: 訊息) -> Dict[str, Any]:
    正反合.ingest(訊息_.text)
    情報 = ""
    try:
        raw = 巡邏者.crawl(["arxiv", "github", "hackernews"])
        項目 = [translate_item(it) for it in raw]
        lines = []
        for it in 項目[:6]:
            title = it.get("title", "") or it.get("標題", "")
            summary = it.get("summary", "") or it.get("摘要", "")
            if title:
                lines.append(f"{title}: {summary}")
        情報 = "\n".join(lines)
    except Exception:
        情報 = ""
    try:
        正, 正src = asyncio.run(正反合.answer(訊息_.text, context=情報))
    except Exception as e:
        正 = _default_thesis(正反合._topic(訊息_.text), 情報); 正src = "本地估算"
    try:
        反, 反src = asyncio.run(antithesis.challenge(正, topic=正反合._topic(訊息_.text), context=情報))
    except Exception as e:
        反 = _default_antithesis(正反合._topic(訊息_.text), 情報); 反src = "本地估算"
    try:
        整合, 整src = asyncio.run(synthesis.fuse(正, 反, topic=正反合._topic(訊息_.text), context=情報))
    except Exception as e:
        整合 = _default_synthesis(正反合._topic(訊息_.text), 情報); 整src = "本地估算"
    return {
        "正方": 正,
        "反方": 反,
        "整合結論": 整合,
        "情報前導": 情報,
        "來源": {"正方": 正src, "反方": 反src, "整合": 整src},
    }


@app.get("/digest")
def 摘要() -> Dict[str, Any]:
    原始 = 巡邏者.crawl(["arxiv", "github", "hackernews"])
    項目 = [translate_item(it) for it in 原始]
    try:
        財務情報 = 財經fetcher.fetch()
        項目.extend([translate_item(it) for it in 財務情報])
    except Exception:
        pass
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

class 會話訊息(BaseModel):
    text: str
    role: str = "user"

@app.get("/sessions")
def 列出會話(api_key: str = "anonymous") -> Dict[str, Any]:
    return {"會話": 會話記憶.list_sessions(api_key)}

@app.post("/sessions/{thread_id}/ingest")
def 會話寫入(thread_id: str, 訊息_: 會話訊息, api_key: str = "anonymous") -> Dict[str, Any]:
    會話記憶.append(api_key, 訊息_.role or "user", 訊息_.text, thread_id=thread_id)
    return {"已儲存": True}

@app.get("/sessions/{thread_id}/recent")
def 會話最近(thread_id: str, api_key: str = "anonymous", limit: int = 20) -> Dict[str, Any]:
    return {"會話": 會話記憶.recent(api_key, thread_id=thread_id, limit=limit)}


@app.post("/peers/align")
def 對齊(資料: 比較) -> Dict[str, Any]:
    結果 = 對齊器.compare(資料.a, 資料.b)
    return {"對齊結果": 結果}


@app.post("/approve")
def 核准(行動_: 行動) -> Dict[str, Any]:
    return {"核准結果": 協同器.approve({"標籤": 行動_.label})}
