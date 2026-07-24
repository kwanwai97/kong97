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

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
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
from backend import identity as identity_module
from backend import auth as auth_module

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
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/dashboard") or request.url.path.startswith("/docs"):
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
身份層 = identity_module.IdentityLayer()

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT.parent / "frontend" / "app" / "components"
DOCS_DIR = ROOT.parent / "docs"
DATA_DIR = ROOT.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/dashboard", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="dashboard")
app.mount("/docs", StaticFiles(directory=str(DOCS_DIR), html=True), name="docs")


class 訊息(BaseModel):
    text: str


class 行動(BaseModel):
    label: str


class 比較(BaseModel):
    a: str
    b: str


class 註冊輸入(BaseModel):
    username: str
    password: str
    display_name: str = ""


class 登入輸入(BaseModel):
    username: str
    password: str


PROTECTED_PREFIXES = ("/identity", "/sessions", "/ingest", "/memory/search")
PUBLIC_PATHS = ("/health", "/brain/status", "/dialectic", "/digest", "/briefing/today") + tuple(f"/auth{r}" for r in ["/register", "/login"])


@app.middleware("http")
async def enforce_auth(request: Request, call_next):
    path = request.url.path
    if any(path == p or path.startswith(p + "/") for p in PROTECTED_PREFIXES):
        token = request.headers.get("X-User-Token", "")
        if not token:
            return JSONResponse(status_code=401, content={"detail": "缺少 X-User-Token"})
        info = auth_module.verify(token)
        if not info:
            return JSONResponse(status_code=401, content={"detail": "無效或已過期的 X-User-Token"})
    return await call_next(request)


async def 取得使用者(x_user_token: str = Header(default="", alias="X-User-Token")) -> Dict[str, Any]:
    if not x_user_token:
        raise HTTPException(status_code=401, detail="缺少 X-User-Token")
    info = auth_module.verify(x_user_token)
    if not info:
        raise HTTPException(status_code=401, detail="無效或已過期的 X-User-Token")
    return {"user_id": info["user_id"], "username": info["username"]}


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
    return RedirectResponse(url="/docs/index.html")


@app.get("/favicon.ico")
def 圖示() -> FileResponse:
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"), status_code=204)


@app.post("/auth/register")
def 註冊(資料: 註冊輸入) -> Dict[str, Any]:
    res = auth_module.register(資料.username.strip(), 資料.password, (資料.display_name or "").strip())
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("error", "註冊失敗"))
    return res


@app.post("/auth/login")
def 登入(資料: 登入輸入) -> Dict[str, Any]:
    res = auth_module.login(資料.username.strip(), 資料.password)
    if not res.get("ok"):
        raise HTTPException(status_code=401, detail=res.get("error", "登入失敗"))
    return res


@app.post("/ingest")
def 存入記憶(訊息_: 訊息, user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
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
def 搜尋記憶(查詢: str, user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    結果 = 記憶體.search(查詢)
    return {"查詢": 查詢, "結果": 結果, "數量": len(結果)}


class 會話訊息(BaseModel):
    text: str
    role: str = "user"


@app.get("/sessions")
def 列出會話(api_key: str = "anonymous", user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    key = user.get("user_id") or api_key
    return {"會話": 會話記憶.list_sessions(key)}


@app.post("/sessions/{thread_id}/ingest")
def 會話寫入(thread_id: str, 訊息_: 會話訊息, api_key: str = "anonymous", user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    key = user.get("user_id") or api_key
    會話記憶.append(key, 訊息_.role or "user", 訊息_.text, thread_id=thread_id)
    return {"已儲存": True}


@app.get("/sessions/{thread_id}/recent")
def 會話最近(thread_id: str, api_key: str = "anonymous", limit: int = 20, user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    key = user.get("user_id") or api_key
    return {"會話": 會話記憶.recent(key, thread_id=thread_id, limit=limit)}


@app.post("/peers/align")
def 對齊(資料: 比較) -> Dict[str, Any]:
    結果 = 對齊器.compare(資料.a, 資料.b)
    return {"對齊結果": 結果}


@app.post("/approve")
def 核准(行動_: 行動) -> Dict[str, Any]:
    return {"核准結果": 協同器.approve({"標籤": 行動_.label})}


# Identity API Routes

@app.get("/identity/profile")
def 取得個人檔案(user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    uid = user["user_id"]
    身份層.ensure_profile(uid)
    return 身份層.get_profile(uid)


@app.patch("/identity/profile")
def 更新個人檔案(資料: Dict[str, Any], user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    uid = user["user_id"]
    return 身份層.update_profile(uid, **資料)


@app.get("/identity/decisions")
def 取得決策紀錄(user: Dict[str, Any] = Depends(取得使用者), limit: int = 50) -> Dict[str, Any]:
    uid = user["user_id"]
    rows = 身份層.list_decisions(uid, limit=limit)
    return {"用戶": uid, "決策": rows}


@app.post("/identity/decisions")
def 新增決策(資料: Dict[str, Any], user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    uid = user["user_id"]
    topic = 資料.get("topic", "")
    choice = 資料.get("choice", "")
    reasoning = 資料.get("reasoning", "")
    tags = 資料.get("tags", []) or []
    if not topic or not choice:
        raise HTTPException(status_code=400, detail="缺少 topic / choice")
    entry = 身份層.record_decision(uid, topic, choice, reasoning=reasoning, tags=tags)
    return entry


@app.post("/identity/decisions/outcome")
def 記錄成果(資料: Dict[str, Any], user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    uid = user["user_id"]
    did = 資料.get("decision_id", "")
    outcome = 資料.get("outcome", "")
    if not did or outcome is None or outcome == "":
        raise HTTPException(status_code=400, detail="缺少 decision_id / outcome")
    return 身份層.record_outcome(uid, did, str(outcome))


@app.get("/identity/blindspots")
def 取得盲點(user: Dict[str, Any] = Depends(取得使用者), status: str = "active") -> Dict[str, Any]:
    uid = user["user_id"]
    rows = 身份層.list_blindspots(uid, status=status)
    return {"用戶": uid, "盲點訊號": rows}


@app.post("/identity/blindspots/analyze")
def 分析盲點(user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    from backend.identity_analyzer import analyze_blindspots
    uid = user["user_id"]
    signals = analyze_blindspots(uid)
    saved = [身份層.add_blindspot_signal(uid, s["pattern"], evidence=s.get("evidence", []), severity=s.get("severity", "medium")) for s in signals]
    return {"用戶": uid, "已產生": saved}


@app.post("/identity/daily-log")
def 新增日誌(資料: Dict[str, Any], user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    uid = user["user_id"]
    entries = 資料.get("entries", [])
    if not isinstance(entries, list) or len(entries) == 0:
        raise HTTPException(status_code=400, detail="entries 為必填")
    return 身份層.append_daily_log(uid, entries)


@app.get("/identity/daily-log")
def 取得日誌(user: Dict[str, Any] = Depends(取得使用者), days: int = 7) -> Dict[str, Any]:
    uid = user["user_id"]
    rows = 身份層.get_daily_log(uid, days=days)
    return {"用戶": uid, "日誌": rows}


@app.post("/identity/facts")
def 設定個人事實(資料: Dict[str, Any], user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    uid = user["user_id"]
    category = str(資料.get("category", ""))
    key = str(資料.get("key", ""))
    value = str(資料.get("value", ""))
    confidence = float(資料.get("confidence", 1.0) or 1.0)
    source = str(資料.get("source", "user_input") or "user_input")
    if not category or not key or value is None or value == "":
        raise HTTPException(status_code=400, detail="category / key / value 為必填")
    return 身份層.set_user_fact(uid, category, key, value, confidence=confidence, source=source)


@app.get("/identity/facts")
def 取得個人事實(user: Dict[str, Any] = Depends(取得使用者), category: str = "") -> Dict[str, Any]:
    uid = user["user_id"]
    cat = category.strip() or None
    rows = 身份層.get_user_facts(uid, category=cat)
    return {"用戶": uid, "事實": rows}


# Proactive Identity Routes

主動者 = None

def _proactive() -> "ProactiveIdentity":
    global 主動者
    if 主動者 is None:
        from backend.proactive_identity import ProactiveIdentity
        主動者 = ProactiveIdentity()
    return 主動者


@app.get("/identity/reminders")
def 取得提醒(user: Dict[str, Any] = Depends(取得使用者), days: int = 14) -> Dict[str, Any]:
    uid = user["user_id"]
    rows = _proactive().list_reminders(uid, days=days)
    return {"用戶": uid, "提醒": rows}


@app.post("/identity/reminders/generate")
def 產生提醒(user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    uid = user["user_id"]
    rows = _proactive().generate_reminders(uid)
    return {"用戶": uid, "已產生": rows}


@app.post("/identity/reminders/{reminder_id}/resolve")
def 解決提醒(reminder_id: str, user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    uid = user["user_id"]
    return _proactive().set_reminder_status(uid, reminder_id, "resolved")


@app.get("/identity/digest")
def 身份摘要(user: Dict[str, Any] = Depends(取得使用者), days: int = 3) -> Dict[str, Any]:
    uid = user["user_id"]
    return _proactive().daily_digest(uid, days=days)


# Backup / Export / Import

@app.get("/identity/backup/export")
def 備份匯出(user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    from backend.backup import save_backup
    uid = user["user_id"]
    return save_backup(uid)


@app.get("/identity/backup/list")
def 備份列表(user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    from backend.backup import list_backups
    uid = user["user_id"]
    return {"用戶": uid, "備份": list_backups(uid)}


@app.post("/identity/backup/import")
def 備份還原(檔案: Dict[str, Any], user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    from backend.backup import import_user
    uid = user["user_id"]
    payload = 檔案.get("payload") or {}
    return import_user(uid, payload)


# Agentic Briefing Route

@app.get("/identity/morning-briefing")
def 晨間簡報(user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    from backend.briefing_agent import morning_briefing
    uid = user["user_id"]
    return morning_briefing(uid)


# Autonomous Mode Routes

@app.post("/identity/autonomous/start")
def 啟動_自主(user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    from backend.autonomous_ingest import get_runner, DROP_DIR
    uid = user["user_id"]
    runner = get_runner(uid)
    runner.start()
    return {"ok": True, "mode": "autonomous", "user_id": uid, "drop_dir": str(DROP_DIR)}


@app.post("/identity/autonomous/stop")
def 停止_自主(user: Dict[str, Any] = Depends(取得使用者)) -> Dict[str, Any]:
    from backend.autonomous_ingest import get_runner
    uid = user["user_id"]
    runner = get_runner(uid)
    runner.stop()
    return {"ok": True, "mode": "stopped", "user_id": uid}


@app.post("/identity/autonomous/capture")
def 快速捕捉(user: Dict[str, Any] = Depends(取得使用者), 資料: Dict[str, Any] = {}) -> Dict[str, Any]:
    from backend.autonomous_ingest import get_runner
    uid = user["user_id"]
    text = str(資料.get("text", "") or "")
    kind = str(資料.get("kind", "quick") or "quick")
    return get_runner(uid).quick_capture(text, kind=kind)
