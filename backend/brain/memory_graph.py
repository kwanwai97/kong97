# -*- coding: utf-8 -*-
"""
記憶圖譜 - 分散式知識庫
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


記憶檔案 = Path(__file__).resolve().parents[2] / "data" / "memory_graph.json"


def 確保檔案() -> None:
    記憶檔案.parent.mkdir(parents=True, exist_ok=True)
    if not 記憶檔案.exists():
        記憶檔案.write_text("[]", encoding="utf-8")


def 雜湊(文字: str) -> str:
    return hashlib.md5(文字.encode("utf-8")).hexdigest()[:10]


class MemoryGraph:
    def __init__(self) -> None:
        確保檔案()

    def load(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(記憶檔案.read_text(encoding="utf-8"))
        except Exception:
            return []

    def save(self, 圖譜: List[Dict[str, Any]]) -> None:
        記憶檔案.write_text(json.dumps(圖譜, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert(self, 節點: Dict[str, Any]) -> None:
        圖譜 = self.load()
        節點.setdefault("id", 雜湊(節點.get("text", "")))
        圖譜.append(節點)
        self.save(圖譜)

    def search(self, 關鍵字: str) -> List[Dict[str, Any]]:
        關鍵字 = 關鍵字.lower()
        return [n for n in self.load() if 關鍵字 in str(n.get("text", "")).lower()]
