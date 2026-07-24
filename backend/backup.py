"""
Backup / export / import for user identity data.
Provides JSON export + import for portability and trust.
"""
from __future__ import annotations

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from backend import identity as identity_module

BASE = Path(__file__).resolve().parents[2]
BACKUP_DIR = BASE / "data" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _id() -> str:
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:12]


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def export_user(user_id: str) -> Dict[str, Any]:
    layer = identity_module.IdentityLayer()
    profile = layer.get_profile(user_id)
    decisions = layer.list_decisions(user_id, limit=2000)
    logs = layer.get_daily_log(user_id, days=3650)
    facts = layer.get_user_facts(user_id, limit=2000)
    blindspots = layer.list_blindspots(user_id, limit=2000)
    return {
        "version": 1,
        "exported_at": _now(),
        "user_id": user_id,
        "profile": profile,
        "decisions": decisions,
        "daily_logs": logs,
        "facts": facts,
        "blindspots": blindspots,
    }


def save_backup(user_id: str) -> Dict[str, Any]:
    payload = export_user(user_id)
    path = BACKUP_DIR / f"{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{_id()}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "path": str(path), "size": path.stat().st_size}


def list_backups(user_id: str) -> List[Dict[str, Any]]:
    out = []
    for p in BACKUP_DIR.glob(f"{user_id}_*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.append({
                "file": p.name,
                "path": str(p),
                "exported_at": data.get("exported_at"),
                "size": p.stat().st_size,
            })
        except Exception:
            continue
    out.sort(key=lambda x: x.get("exported_at") or "", reverse=True)
    return out


def import_user(user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    layer = identity_module.IdentityLayer()
    profile = payload.get("profile") or {}
    if profile.get("user_id") == user_id:
        layer.update_profile(user_id, **{k: v for k, v in profile.items() if k != "user_id"})
    for f in payload.get("facts") or []:
        if f.get("user_id") != user_id:
            continue
        layer.set_user_fact(
            user_id, f.get("category", ""), f.get("key", ""), f.get("value", ""),
            confidence=float(f.get("confidence", 1) or 1),
            source=f.get("source", "import"),
        )
    for d in payload.get("decisions") or []:
        if d.get("user_id") != user_id:
            continue
        layer.record_decision(
            user_id, d.get("topic", ""), d.get("choice", ""),
            reasoning=d.get("reasoning", ""), tags=d.get("tags") or [],
        )
    for entry in payload.get("daily_logs") or []:
        if entry.get("user_id") != user_id:
            continue
        layer.append_daily_log(user_id, entries=entry.get("entries") or [])
    for s in payload.get("blindspots") or []:
        if s.get("user_id") != user_id:
            continue
        layer.add_blindspot_signal(
            user_id, s.get("pattern", ""),
            evidence=s.get("evidence") or [], severity=s.get("severity", "medium"),
        )
    return {"ok": True, "imported": True}
