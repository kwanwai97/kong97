"""
Dialectical Brain - 辯證合夥人核心（非阻塞本地 LLM）
"""
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import List, Tuple

from backend.brain.memory_graph import MemoryGraph


@dataclass
class Thought:
    Text: str
    Role: str = "user"
    TS: float = field(default_factory=time.time)


class LocalLLMClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2:7b") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, messages: List[dict], temperature: float = 0.4, max_tokens: int = 300) -> str:
        import urllib.request
        import json as _json
        payload = _json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            data = _json.loads(r.read().decode("utf-8"))
        return (data.get("message") or {}).get("content", "").strip()


def _default_thesis(topic: str) -> str:
    return (
        f"【正方】\n"
        f"針對「{topic}」而言，短期可能存在正向預期；"
        f"尤其當市場成交量放大、消息面偏多頭時，上升動能較強。\n"
        f"建議持續關注消息面與技術面是否共振。"
    )


def _default_antithesis(topic: str) -> str:
    return (
        f"【反方】\n"
        f"針對「{topic}」而言，仍需警惕回調風險；"
        f"例如消息面反覆、技術面背馳、或成交量未能持續放大時，都可能逆轉。\n"
        f"建議設定止損、避免高槓桿單邊押注。"
    )


def _default_synthesis(topic: str) -> str:
    return (
        f"【整合結論】\n"
        f"針對「{topic}」宜採平衡策略。\n"
        f"1) 順勢為前提，嚴設止損；\n"
        f"2) 觀察成交量、波動率與消息面是否配合；\n"
        f"3) 保留彈性倉位，風險優先。"
    )


class ThesisEngine:
    def __init__(self) -> None:
        self.conversation: List[Thought] = []
        self.memory = MemoryGraph()
        self.model = os.getenv("DIGITAL_TWIN_LLM", "qwen2:7b")
        self.llm = LocalLLMClient(model=self.model)

    def ingest(self, text: str) -> Thought:
        t = Thought(Text=text, Role="user")
        self.conversation.append(t)
        self.memory.upsert({"role": "user", "text": text, "ts": t.TS})
        return t

    def _history(self, limit: int = 6) -> List[dict]:
        return [{"role": c.Role, "content": c.Text} for c in self.conversation[-limit:]]

    def _topic(self, text: str = "") -> str:
        text = (text or "").strip()
        if text:
            return text
        if self.conversation:
            return self.conversation[-1].Text
        return "未知主題"

    async def _llm_or_fallback(self, messages, fallback_fn):
        try:
            text = await asyncio.to_thread(self.llm.chat, messages)
            if not text:
                return fallback_fn()
            return text
        except Exception:
            return fallback_fn()

    async def answer(self, text: str = "") -> Tuple[str, str]:
        topic = self._topic(text)
        messages = [
            {"role": "system", "content": "你是 Digital Twin 的辯證合夥人大腦。只以繁體中文回答。"},
            *self._history(6),
            {"role": "user", "content": f"請針對：{topic}\n用【正方】格式，產出正方的結構化論述。"},
        ]
        text = await self._llm_or_fallback(messages, lambda: _default_thesis(topic))
        return text, topic


class AntithesisEngine:
    def __init__(self) -> None:
        self.llm = LocalLLMClient()

    async def challenge(self, thesis: str, topic: str = "") -> str:
        seed = topic or thesis.split("：")[-1] if "：" in thesis else thesis
        if not seed:
            seed = "當前命題"
        messages = [
            {"role": "system", "content": "你是 Digital Twin 的反方引擎。只以繁體中文提出反向質疑。"},
            {"role": "user", "content": f"請針對正方論述提出【反方】反向質疑：{thesis}"},
        ]
        return await self._llm_or_fallback(messages, lambda: _default_antithesis(seed))

    async def _llm_or_fallback(self, messages, fallback_fn):
        try:
            text = await asyncio.to_thread(self.llm.chat, messages)
            if not text:
                return fallback_fn()
            return text
        except Exception:
            return fallback_fn()


class SynthesisEngine:
    def __init__(self) -> None:
        self.llm = LocalLLMClient()

    async def fuse(self, a: str, b: str, topic: str = "") -> str:
        seed = topic or "當前命題"
        messages = [
            {"role": "system", "content": "你是 Digital Twin 的整合引擎。只以繁體中文產出第三視角結論。"},
            {"role": "user", "content": f"正方：\n{a}\n\n反方：\n{b}\n\n請產出【整合結論】第三視角。"},
        ]
        try:
            text = await asyncio.to_thread(self.llm.chat, messages)
            if not text:
                return _default_synthesis(seed)
            return text
        except Exception:
            return _default_synthesis(seed)
