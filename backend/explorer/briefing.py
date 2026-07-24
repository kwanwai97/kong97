"""
Digest/Briefing utilities
"""
from __future__ import annotations

from typing import List, Dict, Any

from backend.explorer.night_wanderer import NightWanderer
from backend.explorer.translator import translate_briefing

巡邏者 = NightWanderer()


def build_briefing(sources=("arxiv", "github", "hackernews"), translate: bool = False) -> Dict[str, Any]:
    items = 巡邏者.crawl(list(sources))
    
    result: Dict[str, Any] = {
        "生成時間": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "來源": list(sources),
        "項目數量": len(items),
        "項目": items,
        "摘要": 巡邏者.summarize(items),
    }
    
    if translate:
        result = translate_briefing(result)
    
    return result
