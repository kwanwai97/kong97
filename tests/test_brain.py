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
        # pytest-asyncio or other event loops can provide `pytest.mark.asyncio`
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    return asyncio.get_event_loop().run_until_complete(coro)


def test_thesis_ingest_and_answer():
    engine = ThesisEngine()
    t = engine.ingest("AI governance")
    assert isinstance(t, Thought)
    assert t.Text == "AI governance"
    out = _run(engine.answer("AI governance"))
    assert isinstance(out, tuple)
    text = out[0] if out else ""
    # local fallback is used in tests by default
    assert text.startswith("【正方】")


def test_antithesis_challenge_shape():
    engine = AntithesisEngine()
    out = _run(engine.challenge("someone said X"))
    assert out.startswith("【反方】") or "【反方】" in out


def test_synthesis_fuse_shape():
    engine = SynthesisEngine()
    out = _run(engine.fuse("Thesis A", "Antithesis B"))
    assert out.startswith("【整合結論】") or "【整合結論】" in out
