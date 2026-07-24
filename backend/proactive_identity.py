"""
Proactive identity helper.
- generate reminders from decision/log signals
- daily digest summarizing blindspots + queue + open decisions
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import json
import time
import hashlib

from backend.identity_analyzer import analyze_blindspots


BASE = Path(__file__).resolve().parents[2]
DB_PATH = BASE / "data" / "identity.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def _id() -> str:
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:12]


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _ensure() -> None:
    c = _conn()
    c.executescript("""
CREATE TABLE IF NOT EXISTS reminders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    due_at TEXT,
    status TEXT DEFAULT 'open',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_digests (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    date TEXT NOT NULL,
    payload TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);
""")
    c.commit()
    c.close()


_ensure()


class ProactiveIdentity:
    def __init__(self) -> None:
        pass

    def generate_reminders(self, user_id: str, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        if now is None:
            now = datetime.utcnow()
        signals = analyze_blindspots(user_id)
        existing = self.list_reminders(user_id, days=7)
        existing_keys = {(r.get("kind"), r.get("title")) for r in existing}
        out: List[Dict[str, Any]] = []

        def add(kind: str, title: str, body: str = "", due: Optional[str] = None):
            key = (kind, title)
            if key in existing_keys:
                return
            rid = _id()
            c = _conn()
            c.execute(
                "INSERT INTO reminders (id, user_id, kind, title, body, due_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (rid, user_id, kind, title, body, due, _now()),
            )
            c.commit()
            c.close()
            existing_keys.add(key)
            out.append({"id": rid, "kind": kind, "title": title, "body": body, "due_at": due, "status": "open"})

        # Open decisions older than 7 days
        try:
            from backend.identity import IdentityLayer
            rows = IdentityLayer().list_decisions(user_id, limit=200)
            today = datetime.utcnow().date()
            for d in rows:
                created = None
                try:
                    created = datetime.fromisoformat((d.get("created_at") or "").replace("Z", "+00:00")).date()
                except Exception:
                    continue
                if (today - created).days > 7 and (str(d.get("outcome", "") or "").strip() == ""):
                    add("open_decision", f"仍未回填成果：{d.get('topic')}", d.get("choice", ""))
                    break  # 只提醒一次
        except Exception:
            pass

        # Regret/emotion scans
        if any("後悔" in s.get("pattern", "") or "後悔" in json.dumps(s.get("evidence", []), ensure_ascii=False) for s in signals):
            add("reflection", "近期日誌有悔恨訊號", "建議睡前寫：今日最失準嘅判斷點解？")
        if any("decision" in s.get("pattern", "").lower() or "完成率" in s.get("pattern", "") for s in signals):
            add("action", "決策完成率偏低", "下午開 10 分鐘，補回填 3 個舊 decision")

        # Missing facts
        missing = []
        for s in signals:
            ev = s.get("evidence") or {}
            if isinstance(ev, dict):
                missing.extend(ev.get("missing") or [])
        if missing:
            add("identity", "身份事實庫唔完整", "請補齊：" + ", ".join(sorted(set(missing))))

        return out

    def list_reminders(self, user_id: str, days: int = 14, status: str = "open") -> List[Dict[str, Any]]:
        c = _conn()
        rows = c.execute(
            "SELECT * FROM reminders WHERE user_id = ? AND created_at >= ? AND status = ? ORDER BY created_at DESC",
            (user_id, (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z", status),
        ).fetchall()
        c.close()
        return [dict(r) for r in rows]

    def set_reminder_status(self, user_id: str, reminder_id: str, status: str = "resolved") -> Dict[str, Any]:
        c = _conn()
        c.execute("UPDATE reminders SET status = ? WHERE id = ? AND user_id = ?", (status, reminder_id, user_id))
        c.commit()
        r = c.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
        c.close()
        return dict(r) if r else {}

    def daily_digest(self, user_id: str, days: int = 3) -> Dict[str, Any]:
        signals = analyze_blindspots(user_id)
        from backend.identity import IdentityLayer
        layer = IdentityLayer()
        decisions = layer.list_decisions(user_id, limit=200)
        logs = layer.get_daily_log(user_id, days=days)

        comp_rate, with_outcome = _completion_rate(decisions)
        recent_open = [{"id": d.get("id"), "topic": d.get("topic"), "created_at": d.get("created_at")} for d in decisions[:3] if not str(d.get("outcome", "") or "").strip()]
        recent_logs = [r.get("date") for r in logs[:3]]

        top = (signals or [{}])[0]
        tip = top.get("suggestion") or "繼續記錄決策，系統會自動偵測模式"

        summary = {
            "user_id": user_id,
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "signals_count": len(signals) if signals else 0,
            "open_decisions": len([d for d in decisions if not str(d.get("outcome", "") or "").strip()]),
            "completion_rate": comp_rate,
            "recent_open": recent_open,
            "recent_logs": recent_logs,
            "top_signal": (signals or [{}])[0].get("pattern") if signals else "尚無明顯訊號",
            "top_severity": (signals or [{}])[0].get("severity") if signals else "low",
            "proactive_tip": tip,
            "reminders_count": len(self.list_reminders(user_id, days=7)),
        }

        c = _conn()
        c.execute(
            "INSERT INTO daily_digests (id, user_id, date, payload, created_at) VALUES (?, ?, ?, ?, ?)",
            (_id(), user_id, summary["date"], json.dumps(summary, ensure_ascii=False), _now()),
        )
        c.commit()
        c.close()
        return summary

    def mark_resolved(self, user_id: str, reminder_id: str) -> Dict[str, Any]:
        return self.set_reminder_status(user_id, reminder_id, "resolved")


def _completion_rate(decisions: List[Dict[str, Any]]) -> tuple[float, int]:
    if not decisions:
        return 0.0, 0
    with_outcome = sum(1 for d in decisions if str(d.get("outcome", "") or "").strip() not in ("", "無"))
    return round(with_outcome / max(len(decisions), 1), 4), with_outcome
