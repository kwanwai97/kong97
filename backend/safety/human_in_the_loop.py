"""
Safety - Human-in-the-Loop 限制與防護
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


class HumanInTheLoop:
    def approve(self, action: Dict[str, Any]) -> bool:
        now = datetime.utcnow().isoformat() + "Z"
        return {
            "approved": True,
            "reviewed_at": now,
            "action": action,
            "note": "外部批准流程已完成（mock）",
        }
