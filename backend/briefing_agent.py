"""
Morning Briefing API for Digital Twin.
Generates proactive_summary: blindspots + reminders + today's focus.
This is the "assistant AI can't do" feature because:
- It only knows YOUR patterns, not generic advice
- It's private, continuous, and specific to your history
"""
from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime

from backend.identity_analyzer import analyze_blindspots
from backend.proactive_identity import ProactiveIdentity


def morning_briefing(user_id: str) -> Dict[str, Any]:
    proactive = ProactiveIdentity()
    signals = analyze_blindspots(user_id)
    reminders = proactive.generate_reminders(user_id)
    digest = proactive.daily_digest(user_id, days=3)

    open_items = [r for r in reminders if r.get("status") == "open"][:5]
    top = (signals or [{}])[0]
    today_focus = (
        top.get("suggestion")
        or digest.get("proactive_tip")
        or "繼續記錄決策"
    )

    briefing = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "user_id": user_id,
        "today_focus": today_focus,
        "signals_count": len(signals) if signals else 0,
        "top_signal": top.get("pattern") if top else "尚無明顯訊號",
        "top_severity": top.get("severity", "low") if top else "low",
        "reminders_open": len(open_items),
        "reminders": open_items,
        "completion_rate": digest.get("completion_rate", 0.0),
        "open_decisions": digest.get("open_decisions", 0),
        "proactive_tip": digest.get("proactive_tip"),
    }
    return briefing
