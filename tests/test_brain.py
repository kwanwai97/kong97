from __future__ import annotations

import time

import pytest

from backend.brain.thesis import AntithesisEngine, SynthesisEngine, ThesisEngine, Thought


def test_thesis_ingest_and_answer():
    engine = ThesisEngine()
    t = engine.ingest("AI governance")
    assert isinstance(t, Thought)
    assert t.Text == "AI governance"
    assert engine.answer().startswith("[正方/")


def test_antithesis_challenge_shape():
    engine = AntithesisEngine()
    out = engine.challenge("someone said X")
    assert "[反方/" in out


def test_synthesis_fuse_shape():
    engine = SynthesisEngine()
    out = engine.fuse("Thesis A", "Antithesis B")
    assert "[整合/" in out
