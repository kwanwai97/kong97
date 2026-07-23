from __future__ import annotations

import json
import os
import tempfile

import pytest

from backend.brain.memory_graph import MemoryGraph


def test_memory_graph_file_created():
    graph = MemoryGraph()
    graph.upsert({"text": "hello"})
    nodes = graph.load()
    assert any(n.get("text") == "hello" for n in nodes)


def test_memory_graph_search():
    from backend.brain.memory_graph import 記憶檔案
    if 記憶檔案.exists():
        記憶檔案.write_text("[]", encoding="utf-8")
    graph = MemoryGraph()
    graph.upsert({"text": "digital twin"})
    graph.upsert({"text": "trading system"})
    hits = graph.search("digital")
    assert len(hits) == 1
    assert hits[0]["text"] == "digital twin"
