"""
Static Dashboard 入口
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI(title="Digital Twin Dashboard")

INDEX = Path(__file__).resolve().parents[2] / "frontend" / "app" / "components" / "dashboard.html"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(INDEX)
