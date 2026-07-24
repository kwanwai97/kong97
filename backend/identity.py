# -*- coding: utf-8 -*-
"""
User Identity Layer - per-user identity profiles, decisions, blindspots, daily logs
Uses SQLite for multi-user isolation.
"""
from __future__ import annotations

import sqlite3
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE = Path(__file__).resolve().parents[2]
DB_PATH = BASE / "data" / "identity.db"


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def _init() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = _conn()
    c.executescript("""
CREATE TABLE IF NOT EXISTS identity_profile (
    user_id TEXT PRIMARY KEY,
    risk_tolerance TEXT DEFAULT 'medium',
    time_horizon TEXT DEFAULT 'medium',
    values_tags TEXT DEFAULT '[]',
    preferred_models TEXT DEFAULT '[]',
    blindspot_flags TEXT DEFAULT '[]',
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    choice TEXT NOT NULL,
    reasoning TEXT DEFAULT '',
    outcome TEXT DEFAULT '',
    outcome_recorded_at TEXT,
    tags TEXT DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS blindspot_signals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    pattern TEXT NOT NULL,
    evidence TEXT DEFAULT '[]',
    severity TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    date TEXT NOT NULL,
    entries TEXT DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_facts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source TEXT DEFAULT 'user_input',
    updated_at TEXT NOT NULL
);
""")
    c.commit()
    c.close()


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _id() -> str:
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:12]


class IdentityLayer:
    def __init__(self) -> None:
        _init()

    def ensure_profile(self, user_id: str, display_name: str = "") -> Dict[str, Any]:
        c = _conn()
        row = c.execute("SELECT user_id FROM identity_profile WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            c.execute(
                "INSERT INTO identity_profile (user_id, updated_at) VALUES (?, ?)",
                (user_id, now_iso()),
            )
            c.commit()
            c.close()
        c.close()
        return self.get_profile(user_id)

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        c = _conn()
        r = c.execute("SELECT * FROM identity_profile WHERE user_id = ?", (user_id,)).fetchone()
        c.close()
        if not r:
            return {"user_id": user_id, "risk_tolerance": "medium", "time_horizon": "medium", "values_tags": [], "preferred_models": [], "blindspot_flags": []}
        return dict(r)

    def update_profile(self, user_id: str, **fields) -> Dict[str, Any]:
        allowed = {"risk_tolerance", "time_horizon", "values_tags", "preferred_models", "blindspot_flags"}
        sets = []
        vals = []
        for k, v in fields.items():
            if k in allowed:
                if isinstance(v, (list, dict)):
                    v = json.dumps(v, ensure_ascii=False)
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return self.get_profile(user_id)
        sets.append("updated_at = ?")
        vals.extend([now_iso(), user_id])
        c = _conn()
        c.execute(f"UPDATE identity_profile SET {', '.join(sets)} WHERE user_id = ?", vals)
        c.commit()
        c.close()
        return self.get_profile(user_id)

    def record_decision(self, user_id: str, topic: str, choice: str, reasoning: str = "", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        did = _id()
        entry = {"id": did, "user_id": user_id, "topic": topic, "choice": choice, "reasoning": reasoning, "tags": tags or [], "created_at": now_iso()}
        c = _conn()
        c.execute(
            "INSERT INTO decisions (id, user_id, topic, choice, reasoning, outcome_recorded_at, tags, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (did, user_id, topic, choice, reasoning, None, json.dumps(tags or [], ensure_ascii=False), now_iso()),
        )
        c.commit()
        c.close()
        return entry

    def list_decisions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        c = _conn()
        rows = c.execute("SELECT * FROM decisions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
        c.close()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["tags"] = json.loads(d.get("tags") or "[]")
            except Exception:
                d["tags"] = []
            out.append(d)
        return out

    def record_outcome(self, user_id: str, decision_id: str, outcome: str) -> Dict[str, Any]:
        c = _conn()
        c.execute("UPDATE decisions SET outcome = ?, outcome_recorded_at = ? WHERE id = ? AND user_id = ?", (outcome, now_iso(), decision_id, user_id))
        c.commit()
        r = c.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
        c.close()
        return dict(r) if r else {}

    def add_blindspot_signal(self, user_id: str, pattern: str, evidence: Optional[List[str]] = None, severity: str = "medium") -> Dict[str, Any]:
        sid = _id()
        c = _conn()
        c.execute("INSERT INTO blindspot_signals (id, user_id, pattern, evidence, severity, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (sid, user_id, pattern, json.dumps(evidence or [], ensure_ascii=False), severity, "active", now_iso()))
        c.commit()
        c.close()
        return {"id": sid, "user_id": user_id, "pattern": pattern, "severity": severity, "status": "active", "created_at": now_iso()}

    def list_blindspots(self, user_id: str, status: str = "active", limit: int = 100) -> List[Dict[str, Any]]:
        c = _conn()
        rows = c.execute("SELECT * FROM blindspot_signals WHERE user_id = ? AND status = ? ORDER BY created_at DESC LIMIT ?", (user_id, status, limit)).fetchall()
        c.close()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["evidence"] = json.loads(d.get("evidence") or "[]")
            except Exception:
                d["evidence"] = []
            out.append(d)
        return out

    def mark_blindspot_resolved(self, user_id: str, signal_id: str) -> Dict[str, Any]:
        c = _conn()
        c.execute("UPDATE blindspot_signals SET status = 'resolved' WHERE id = ? AND user_id = ?", (signal_id, user_id))
        c.commit()
        r = c.execute("SELECT * FROM blindspot_signals WHERE id = ?", (signal_id,)).fetchone()
        c.close()
        return dict(r) if r else {}

    def append_daily_log(self, user_id: str, entries: Optional[List[str]] = None) -> Dict[str, Any]:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        c = _conn()
        row = c.execute("SELECT id, entries FROM daily_logs WHERE user_id = ? AND date = ?", (user_id, today)).fetchone()
        existing = []
        if row:
            existing = json.loads(row["entries"] or "[]")
            lid = row["id"]
        else:
            lid = _id()
        if entries:
            existing.extend(entries)
        c.execute(
            "INSERT INTO daily_logs (id, user_id, date, entries, created_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET entries = excluded.entries",
            (lid, user_id, today, json.dumps(existing, ensure_ascii=False), now_iso()),
        )
        c.commit()
        c.close()
        return {"user_id": user_id, "date": today, "entries": existing}

    def get_daily_log(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        c = _conn()
        rows = c.execute("SELECT * FROM daily_logs WHERE user_id = ? AND date >= date('now', ?) ORDER BY date DESC", (user_id, f"-{days} days")).fetchall()
        c.close()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["entries"] = json.loads(d.get("entries") or "[]")
            except Exception:
                d["entries"] = []
            out.append(d)
        return out

    def set_user_fact(self, user_id: str, category: str, key: str, value: str, confidence: float = 1.0, source: str = "user_input") -> Dict[str, Any]:
        fid = hashlib.md5(f"{user_id}:{category}:{key}".encode()).hexdigest()[:12]
        c = _conn()
        c.execute("INSERT INTO user_facts (id, user_id, category, key, value, confidence, source, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET value = excluded.value, confidence = excluded.confidence, source = excluded.source, updated_at = excluded.updated_at",
                  (fid, user_id, category, key, value, confidence, source, now_iso()))
        c.commit()
        c.close()
        return {"id": fid, "user_id": user_id, "category": category, "key": key, "value": value, "confidence": confidence, "source": source, "updated_at": now_iso()}

    def get_user_facts(self, user_id: str, category: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        c = _conn()
        if category:
            rows = c.execute("SELECT * FROM user_facts WHERE user_id = ? AND category = ? ORDER BY updated_at DESC LIMIT ?", (user_id, category, limit)).fetchall()
        else:
            rows = c.execute("SELECT * FROM user_facts WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?", (user_id, limit)).fetchall()
        c.close()
        return [dict(r) for r in rows]
