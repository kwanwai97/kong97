"""
Paywall / usage limiter for Digital Twin commercial tier gating.
Free tier limitations:
- 50 decisions max
- 7-day backup retention
- Manual blindspot analysis only (no morning briefing)
"""
from __future__ import annotations

import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from backend import identity as identity_module
from backend import auth as auth_module

TOTAL_LIMITS: Dict[str, int] = {}
BACKUP_RETENTION: Dict[str, int] = {}
if os.getenv("DIGITAL_TWIN_PAYWALL"):
    TOTAL_LIMITS = {"decisions": 50, "facts": 100, "logs": 200}
    BACKUP_RETENTION = 7

def get_tier(user_id: str) -> str:
    return "pro" if user_id in os.getenv("DIGITAL_TWIN_PRO_USERS", "").split(",") else "free"

def get_limits(user_id: str) -> Dict[str, Any]:
    tier = get_tier(user_id)
    if tier == "pro":
        return {"tier": "pro", "decisions": -1, "backup_retention_days": 365, "morning_briefing": True, "autonomous_capture": True}
    return {"tier": "free", **TOTAL_LIMITS, "backup_retention_days": BACKUP_RETENTION.get("backup_retention", 7), "morning_briefing": False, "autonomous_capture": False}

def get_usage(user_id: str) -> Dict[str, int]:
    try:
        il = identity_module.IdentityLayer()
        return {
            "decisions": len(il.list_decisions(user_id) or []),
            "facts": len(il.get_user_facts(user_id) or []),
            "logs": len(il.get_daily_log(user_id, days=9999) or []),
        }
    except Exception:
        return {"decisions": 0, "facts": 0, "logs": 0}

def enforce(user_id: str, resource: str = "decisions") -> Dict[str, Any]:
    limits = get_limits(user_id)
    tier = limits.get("tier", "free")
    if tier == "pro":
        return {"allowed": True, "tier": "pro", "limit": -1}
    limit = limits.get(resource, -1)
    if limit < 0:
        return {"allowed": True, "tier": "free", "limit": -1}
    usage = get_usage(user_id)
    current = usage.get(resource, 0)
    if current >= limit:
        return {"allowed": False, "tier": "free", "limit": limit, "used": current, "resource": resource, "upgrade_url": "/frontend/landing.html"}
    return {"allowed": True, "tier": "free", "limit": limit, "used": current, "remaining": limit - current}

def cleanup_old_backups() -> int:
    if not BACKUP_RETENTION:
        return 0
    cutoff = datetime.utcnow() - timedelta(days=BACKUP_RETENTION.get("backup_retention", 7))
    backup_dir = identity_module.IdentityLayer().DB_PATH.parent / "backups"
    if not backup_dir.exists():
        return 0
    removed = 0
    for path in backup_dir.glob("*.json"):
        try:
            ts = datetime.fromisoformat(path.stem.split("_")[-1].replace("Z", ""))
            if ts < cutoff:
                path.unlink(missing_ok=True)
                removed += 1
        except Exception:
            continue
    return removed
