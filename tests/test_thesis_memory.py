from __future__ import annotations

import json
import os
import tempfile

import pytest

from backend.brain.thesis import ThesisEngine


def test_thesis_persists_to_memory_file():
    engine = ThesisEngine()
    engine.ingest("open-source licensing 001")
    hits = engine.memory.search("open-source")
    assert len(hits) >= 1
    assert any(h.get("text") == "open-source licensing 001" for h in hits)
