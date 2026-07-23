"""
Dialectical Brain - 辯證合夥人核心（可接 real LLM）
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import List

from backend.brain.memory_graph import MemoryGraph


@dataclass
class Thought:
    Text: str
    Role: str = "user"
    TS: float = field(default_factory=time.time)


class ThesisEngine:
    def __init__(self) -> None:
        self.conversation: List[Thought] = []
        self.memory = MemoryGraph()
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("DIGITAL_TWIN_MODEL", "gpt-4o-mini")
        self.use_real = bool(self.api_key)

    def ingest(self, text: str) -> Thought:
        t = Thought(Text=text, Role="user")
        self.conversation.append(t)
        self.memory.upsert({"role": "user", "text": text, "ts": t.TS})
        return t

    def _history(self, limit: int = 6) -> List[dict]:
        return [{"role": c.Role, "content": c.Text} for c in self.conversation[-limit:]]

    def answer(self) -> str:
        if not self.use_real:
            ctx = " | ".join([c.Text for c in self.conversation[-5:]])
            return f"[Thesis/mock] 根據最近 {len(self.conversation)} 則輸入，眼下討論重心為：{ctx}"

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            msgs = [{"role": "system", "content": "你是辯證合夥人的正方引擎，給出具體、可質疑的命題。"}] + self._history(6)
            r = client.chat.completions.create(model=self.model, messages=msgs, temperature=0.35)
            text = (r.choices[0].message.content or "").strip()
            if not text:
                raise RuntimeError("empty completion")
            return text
        except Exception:
            ctx = " | ".join([c.Text for c in self.conversation[-5:]])
            return f"[Thesis/fallback] 根據最近 {len(self.conversation)} 則輸入，眼下討論重心為：{ctx}"


class AntithesisEngine:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("DIGITAL_TWIN_MODEL", "gpt-4o-mini")
        self.use_real = bool(self.api_key)

    def challenge(self, thesis: str) -> str:
        if not self.use_real:
            seed = thesis.split("：")[-1] if "：" in thesis else thesis
            return f"[Antithesis/mock] 命題『{seed[:40]}』可能忽略反面證據，請列出關鍵反例。"

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            msgs = [
                {"role": "system", "content": "你是辯證合夥人的反方引擎，用反向質疑挑戰命題。"},
                {"role": "user", "content": f"請針對以下命題提出反向質疑：{thesis}"},
            ]
            r = client.chat.completions.create(model=self.model, messages=msgs, temperature=0.45)
            text = (r.choices[0].message.content or "").strip()
            return text or f"[Antithesis/fallback] 針對：{thesis[:40]}..."
        except Exception:
            return f"[Antithesis/fallback] 針對：{thesis[:40]}..."


class SynthesisEngine:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("DIGITAL_TWIN_MODEL", "gpt-4o-mini")
        self.use_real = bool(self.api_key)

    def fuse(self, a: str, b: str) -> str:
        if not self.use_real:
            return "[Synthesis/mock] 保留正反核心，放寬前提條件，形成第三視角命題。"

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            msgs = [
                {"role": "system", "content": "你是辯證合夥人的整合引擎，產生第三視角結論。"},
                {"role": "user", "content": f"Thesis:\n{a}\n\nAntithesis:\n{b}\n\n請產出第三視角結論。"},
            ]
            r = client.chat.completions.create(model=self.model, messages=msgs, temperature=0.5)
            text = (r.choices[0].message.content or "").strip()
            return text or "[Synthesis/fallback] 保留正反核心，放寬前提條件。"
        except Exception:
            return "[Synthesis/fallback] 保留正反核心，放寬前提條件。"
