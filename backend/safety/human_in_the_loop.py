"""
Human-in-the-Loop 限制與防護
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


class HumanInTheLoop:
    def approve(self, action: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat() + "Z"
        return {
            "已核准": True,
            "核准時間": now,
            "行動": action,
            "備註": "外部核准流程已完成（模擬）",
        }
