"""
會話記憶 - 多用戶長期對話記憶庫
以 API key 指紋分用戶 / 會話；本地 SQLite 儲存。
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "session_memory.db"


def _ensure() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    title TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    summary TEXT
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );
                """
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_key, thread_id);"
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id, created_at);"
            )
            con.commit()


def fingerprint(key: str) -> str:
    if not key:
        return "anonymous"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


class SessionMemory:
    def __init__(self) -> None:
        _ensure()

    def ensure_session(self, user_key: str, thread_id: Optional[str] = None) -> int:
        user_key = fingerprint(user_key or "")
        thread_id = thread_id or "default"
        now = datetime.datetime.utcnow().isoformat() + "Z"
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute(
                "SELECT id FROM sessions WHERE user_key=? AND thread_id=?",
                (user_key, thread_id),
            ).fetchone()
            if row:
                sid = row[0]
                con.execute(
                    "UPDATE sessions SET updated_at=? WHERE id=?",
                    (now, sid),
                )
            else:
                con.execute(
                    "INSERT INTO sessions(user_key, thread_id, title, created_at, updated_at) VALUES(?,?,?,?,?)",
                    (user_key, thread_id, thread_id, now, now),
                )
                sid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
            con.commit()
            return sid

    def append(self, user_key: str, role: str, content: str, thread_id: Optional[str] = None) -> None:
        sid = self.ensure_session(user_key, thread_id)
        now = datetime.datetime.utcnow().isoformat() + "Z"
        with sqlite3.connect(DB_PATH) as con:
            con.execute(
                "INSERT INTO turns(session_id, role, content, created_at) VALUES(?,?,?,?)",
                (sid, role, content, now),
            )
            con.execute(
                "UPDATE sessions SET updated_at=? WHERE id=?",
                (now, sid),
            )
            con.commit()

    def recent(self, user_key: str, thread_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        sid = self._session_id(user_key, thread_id)
        if not sid:
            return []
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute(
                "SELECT role, content, created_at FROM turns WHERE session_id=? ORDER BY created_at DESC LIMIT ?",
                (sid, limit),
            ).fetchall()
        return [{"role": r, "content": c, "created_at": t} for r, c, t in reversed(rows)]

    def summarize_old(self, user_key: str, thread_id: Optional[str] = None, keep_last: int = 20) -> Optional[str]:
        sid = self._session_id(user_key, thread_id)
        if not sid:
            return None
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute("SELECT summary FROM sessions WHERE id=?", (sid,)).fetchone()
            if row and row[0]:
                return row[0]
            old = con.execute(
                "SELECT role, content FROM turns WHERE session_id=? ORDER BY created_at ASC LIMIT -1 OFFSET ?",
                (sid, keep_last),
            ).fetchall()
        if not old:
            return None
        lines = [f"{r}: {c[:120]}" for r, c in old[:50]]
        text = "\n".join(lines)
        with sqlite3.connect(DB_PATH) as con:
            con.execute("UPDATE sessions SET summary=? WHERE id=?", (text, sid))
            con.commit()
        return text

    def list_sessions(self, user_key: str) -> List[Dict[str, Any]]:
        uk = fingerprint(user_key or "")
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute(
                "SELECT id, thread_id, title, created_at, updated_at FROM sessions WHERE user_key=? ORDER BY updated_at DESC",
                (uk,),
            ).fetchall()
        return [
            {
                "id": r[0],
                "thread_id": r[1],
                "title": r[2],
                "created_at": r[3],
                "updated_at": r[4],
            }
            for r in rows
        ]

    def _session_id(self, user_key: str, thread_id: Optional[str]) -> Optional[int]:
        uk = fingerprint(user_key or "")
        tid = thread_id or "default"
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute(
                "SELECT id FROM sessions WHERE user_key=? AND thread_id=?",
                (uk, tid),
            ).fetchone()
        return row[0] if row else None
