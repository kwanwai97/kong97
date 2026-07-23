"""
Peer Alignment - AI 與 AI 的校準 / 交換介面
"""
from __future__ import annotations

from typing import List


class PeerAlignment:
    def compare(self, a: str, b: str) -> str:
        sa, sb = len(a), len(b)
        delta = abs(sa - sb) / max(1, max(sa, sb))
        return f"對齊差異：{delta:.2f}；長度甲：{sa}；長度乙：{sb}"
