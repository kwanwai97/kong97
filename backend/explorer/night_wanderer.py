"""
Night Wanderer - 夜間巡邏 / 自主探索骨架
"""
from __future__ import annotations

import time
from typing import Iterable, List


class NightWanderer:
    def crawl(self, sources: Iterable[str]) -> List[str]:
        return [f"已取得摘要：{s}" for s in sources]
