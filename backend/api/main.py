"""
API - 系統對外入口
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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
from backend.safety.human_in_the_loop import HumanInTheLoop

app = FastAPI(title="Digital Twin API")

thesis = ThesisEngine()
memory = MemoryGraph()
wanderer = NightWanderer()
peers = PeerAlignment()
hitl = HumanInTheLoop()

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend" / "app" / "components"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/dashboard", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="dashboard")


class Message(BaseModel):
    text: str


class Action(BaseModel):
    label: str


class Compare(BaseModel):
    a: str
    b: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/dashboard.html")


@app.get("/favicon.ico")
def favicon() -> FileResponse:
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"), status_code=204)


@app.post("/ingest")
def ingest(msg: Message) -> Dict[str, Any]:
    t = thesis.ingest(msg.text)
    return {"saved": True, "thought_id": getattr(t, "TS", None)}


@app.post("/dialectic")
def dialectic(msg: Message) -> Dict[str, Any]:
    thesis.ingest(msg.text)
    t_out = thesis.answer()
    a_out = antithesis.challenge(t_out)
    s_out = synthesis.fuse(t_out, a_out)
    return {"thesis": t_out, "antithesis": a_out, "synthesis": s_out}


@app.get("/digest")
def digest() -> Dict[str, Any]:
    raw = wanderer.crawl(["arxiv", "github", "hackernews"])
    summary = wanderer.summarize(raw)
    return {"digests": raw, "summary": summary}


@app.get("/briefing/today")
def briefing_today() -> Dict[str, Any]:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    path = DATA_DIR / f"briefing_{date_str}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    data = build_briefing()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


@app.post("/schedule/briefing")
def schedule_briefing() -> Dict[str, Any]:
    path = DATA_DIR / "briefing_latest.json"
    data = build_briefing()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"saved": True, "path": str(path), "item_count": len(data.get("items", []))}


@app.get("/memory/search")
def memory_search(q: str) -> Dict[str, Any]:
    hits = memory.search(q)
    return {"query": q, "hits": hits, "count": len(hits)}


@app.post("/peers/align")
def peer_align(payload: Compare) -> Dict[str, Any]:
    result = peers.compare(payload.a, payload.b)
    return {"alignment": result}


@app.post("/approve")
def approve(action: Action) -> Dict[str, Any]:
    return {"approved": hitl.approve({"label": action.label})}
