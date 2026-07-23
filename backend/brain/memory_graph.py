"""
Memory Graph - 分散式知識圖譜與向量資料庫
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


MEMORY_FILE = Path(__file__).resolve().parents[2] / "data" / "memory_graph.json"


def ensure_memory_file() -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text("[]", encoding="utf-8")


def hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:10]


class MemoryGraph:
    def __init__(self) -> None:
        ensure_memory_file()

    def load(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

    def save(self, graph: List[Dict[str, Any]]) -> None:
        MEMORY_FILE.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert(self, node: Dict[str, Any]) -> None:
        graph = self.load()
        node.setdefault("id", hash_text(node.get("text", "")))
        graph.append(node)
        self.save(graph)

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        k = keyword.lower()
        return [n for n in self.load() if k in str(n.get("text", "")).lower()]
