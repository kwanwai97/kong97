"""
Digest/Briefing utilities
"""
from __future__ import annotations

from typing import List

from backend.explorer.night_wanderer import NightWanderer

巡邏者 = NightWanderer()


def build_briefing(sources=("arxiv", "github", "hackernews")) -> dict:
    items = 巡邏者.crawl(list(sources))
    return {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "sources": list(sources),
        "item_count": len(items),
        "items": items,
        "summary": 巡邏者.summarize(items),
    }
