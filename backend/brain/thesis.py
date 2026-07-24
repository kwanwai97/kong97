"""
Dialectical Brain - 辯證合夥人核心（非阻塞本地 LLM + 情報聯結）
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
    def __init__(self, base_url: str = "", model: str = "", openai_api_key: str = "") -> None:
        self.base_url = (base_url or os.getenv("DIGITAL_TWIN_LLM_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("DIGITAL_TWIN_LLM_MODEL", "qwen2:7b")
        self.openai_api_key = (openai_api_key or os.getenv("OPENAI_API_KEY", "")).strip()

    def chat(self, messages: List[dict], temperature: float = 0.4, max_tokens: int = 400) -> str:
        if self.openai_api_key:
            try:
                import openai
                client = openai.OpenAI(api_key=self.openai_api_key)
                completion = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return (completion.choices[0].message.content or "").strip()
            except Exception:
                pass
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
        with urllib.request.urlopen(req, timeout=90) as r:
            data = _json.loads(r.read().decode("utf-8"))
        return (data.get("message") or {}).get("content", "").strip()


def _default_thesis(topic: str, context: str = "") -> str:
    lead = ""
    if context:
        lead = f"根據現有情報：{context[:220]}\n"
    return (
        f"【正方】\n"
        f"{lead}"
        f"針對「{topic}」，從現實可行性、數據證據或成功條件看，有支持的面向。\n"
        f"支持點：1) 已有正面指標或先例；2) 假設成立時可量化預期；3) 成本與風險在可承受範圍。\n"
        f"操作條件：若成交量/消息面/政策訊號同步，短線偏多；應保留止損。"
    )


def _default_antithesis(topic: str, context: str = "") -> str:
    lead = ""
    if context:
        lead = f"但情報同時顯示：{context[:220]}\n"
    return (
        f"【反方】\n"
        f"{lead}"
        f"針對「{topic}」，需警惕相反證據、執行高成本或系統性風險。\n"
        f"反證：1) 歷史個案曾出現逆轉；2) 嚴重依赖單一行為；3) 黑天鵝或流动性衝擊時防守不足。\n"
        f"條件：若消息面反覆、技術面背馳、數據放緩，避免重倉單邊。"
    )


def _default_synthesis(topic: str, context: str = "") -> str:
    lead = ""
    if context:
        lead = f"結合情報線索：{context[:180]}\n"
    return (
        f"【整合結論】\n"
        f"{lead}"
        f"針對「{topic}」，最穩妥立場是條件式立場。\n"
        f"前提：成交量、消息面、數據面須共振。\n"
        f"下一步：1) 追蹤確認指標；2) 設定觸發條件與止損；3) 保留彈性倉位並記錄每次判斷、事後覆盤。"
    )


class ThesisEngine:
    def __init__(self) -> None:
        self.conversation: List[Thought] = []
        self.memory = MemoryGraph()
        self.model = os.getenv("DIGITAL_TWIN_LLM", "qwen2:7b")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        self.llm = LocalLLMClient(model=self.model, openai_api_key=openai_key)

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
            if not text or len(text.strip()) < 20:
                return fallback_fn(), "本地估算"
            return text, "本地LLM"
        except Exception:
            return fallback_fn(), "本地估算"

    async def answer(self, text: str = "", context: str = "") -> Tuple[str, str]:
        topic = self._topic(text)
        messages = [
            {"role": "system", "content": "你是 Digital Twin 的正方辯證夥伴。只以繁體中文回答。先判斷主題所屬領域，再給出具體、可檢驗、可操作的結構化論述。避免泛泛而談，必要時引用情報線索。"},
            {"role": "user", "content": f"主旨：{topic}\n情報線索：{context}\n請只輸出【正方】見解，包含：(1) 支持論據 (2) 所需條件 (3) 可觀察指標。"},
        ]
        text, src = await self._llm_or_fallback(messages, lambda: _default_thesis(topic, context))
        return text, src

    async def last_source(self) -> str:
        return "LLM"


class AntithesisEngine:
    def __init__(self) -> None:
        self.llm = LocalLLMClient()

    async def _llm_or_fallback(self, messages, fallback_fn):
        try:
            text = await asyncio.to_thread(self.llm.chat, messages)
            if not text or len(text.strip()) < 20:
                return fallback_fn(), "本地估算"
            return text, "本地LLM"
        except Exception:
            return fallback_fn(), "本地估算"

    async def challenge(self, thesis: str, topic: str = "", context: str = "") -> Tuple[str, str]:
        seed = topic or thesis.split("：")[-1] if "：" in thesis else thesis
        if not seed:
            seed = "當前命題"
        messages = [
            {"role": "system", "content": "你是 Digital Twin 的反方辯證夥伴。只以繁體中文提出可檢驗的反對理由，要求具體、有邊界條件、有操作警示。"},
            {"role": "user", "content": f"主旨：{seed}\n情報線索：{context}\n請只輸出【反方】反向質疑，包含：(1) 反證 (2) 代理問題或成本 (3) 何時應放棄原假設。"},
        ]
        return await self._llm_or_fallback(messages, lambda: _default_antithesis(seed, context))


class SynthesisEngine:
    def __init__(self) -> None:
        self.llm = LocalLLMClient()

    async def _llm_or_fallback(self, messages, fallback_fn):
        try:
            text = await asyncio.to_thread(self.llm.chat, messages)
            if not text or len(text.strip()) < 20:
                return fallback_fn(), "本地估算"
            return text, "本地LLM"
        except Exception:
            return fallback_fn(), "本地估算"

    async def fuse(self, a: str, b: str, topic: str = "", context: str = "") -> Tuple[str, str]:
        seed = topic or "當前命題"
        messages = [
            {"role": "system", "content": "你是 Digital Twin 的整合辯證夥伴。只以繁體中文產出第三視角結論，要求：(1) 標明成立前提 (2) 可操作步驟 (3) 證據缺口。"},
            {"role": "user", "content": f"主旨：{seed}\n情報線索：{context}\n正方：\n{a}\n\n反方：\n{b}\n\n請輸出【整合結論】。"},
        ]
        return await self._llm_or_fallback(messages, lambda: _default_synthesis(seed, context))
