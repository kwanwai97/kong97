from __future__ import annotations

import asyncio

import pytest

from backend.brain.thesis import AntithesisEngine, SynthesisEngine, ThesisEngine, Thought


def _run(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    return asyncio.get_event_loop().run_until_complete(coro)


def test_thesis_ingest_and_answer():
    engine = ThesisEngine()
    t = engine.ingest("AI governance")
    assert isinstance(t, Thought)
    assert t.Text == "AI governance"
    out = _run(engine.answer("AI governance", context="情報: AI治理需要在安全與創新間平衡。"))
    assert isinstance(out, tuple)
    text, src = out
    assert "【正方】" in text


def test_antithesis_challenge_shape():
    engine = AntithesisEngine()
    out = _run(engine.challenge("some thesis", topic="AI governance"))
    assert isinstance(out, tuple)
    text, src = out
    assert "【反方】" in text


def test_synthesis_fuse_shape():
    engine = SynthesisEngine()
    out = _run(engine.fuse("Thesis A", "Antithesis B", topic="AI governance"))
    assert isinstance(out, tuple)
    text, src = out
    assert "【整合結論】" in text
