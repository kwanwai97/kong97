"""
Dialectical Brain - 辯證合夥人核心
"""
from __future__ import annotations

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

    def _topic(self, text: str = "") -> str:
        text = (text or "").strip()
        if text:
            return text
        if self.conversation:
            return self.conversation[-1].Text
        return "未知主題"

    def answer(self, text: str = "") -> Tuple[str, str]:
        topic = self._topic(text)

        def local_thesis(t: str) -> str:
            return (
                f"【正方】\n"
                f"針對「{t}」而言，若消息面偏多頭、技術面出現破位，短期往往存在正向預期；"
                f"尤其當市場成交量放大、資金流入明顯時，上升動能較強。\n"
                f"建議持續關注消息面與技術面是否共振。"
            )

        if not self.use_real:
            return local_thesis(topic), topic

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            msgs = [{"role": "system", "content": "你是辯證合夥人的正方引擎，給出具體、可質疑的命題。"}] + self._history(6)
            r = client.chat.completions.create(model=self.model, messages=msgs, temperature=0.35)
            text = (r.choices[0].message.content or "").strip()
            if text:
                return text, topic
            return local_thesis(topic), topic
        except Exception:
            return local_thesis(topic), topic


class AntithesisEngine:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("DIGITAL_TWIN_MODEL", "gpt-4o-mini")
        self.use_real = bool(self.api_key)

    def challenge(self, thesis: str, topic: str = "") -> str:
        seed = topic or thesis.split("：")[-1] if "：" in thesis else thesis
        if not seed:
            seed = "當前命題"

        def local_antithesis(t: str) -> str:
            return (
                f"【反方】\n"
                f"針對「{t}」而言，即便趨勢偏多，仍要警惕回調風險；"
                f"例如消息面反覆、技術面出現背馳、或成交量未能持續放大時，都可能導致走勢逆轉。\n"
                f"建議設定止損位、避免高槓桿單邊押注。"
            )

        if not self.use_real:
            return local_antithesis(seed)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            msgs = [
                {"role": "system", "content": "你是辯證合夥人的反方引擎，用反向質疑挑戰命題。"},
                {"role": "user", "content": f"請針對以下命題提出反向質疑：{thesis}"},
            ]
            r = client.chat.completions.create(model=self.model, messages=msgs, temperature=0.45)
            text = (r.choices[0].message.content or "").strip()
            return text or local_antithesis(seed)
        except Exception:
            return local_antithesis(seed)


class SynthesisEngine:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("DIGITAL_TWIN_MODEL", "gpt-4o-mini")
        self.use_real = bool(self.api_key)

    def fuse(self, a: str, b: str, topic: str = "") -> str:
        seed = topic or "當前命題"

        def local_synthesis(t: str) -> str:
            return (
                f"【整合結論】\n"
                f"針對「{t}」宜採平衡策略：\n"
                f"1) 順勢為前提下，嚴設止損，避免重倉單邊；\n"
                f"2) 同時觀察成交量、波動率與消息面是否配合；\n"
                f"3) 若信號 conflicting，優先保留彈性倉位，勝過單邊豪賭。\n"
                f"综合而言，方向上留有空間，但嚴格把風險放在首位。"
            )

        if not self.use_real:
            return local_synthesis(seed)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            msgs = [
                {"role": "system", "content": "你是辯證合夥人的整合引擎，產生第三視角結論。"},
                {"role": "user", "content": f"正方論述：\n{a}\n\n反方論述：\n{b}\n\n請產出第三視角結論。"},
            ]
            r = client.chat.completions.create(model=self.model, messages=msgs, temperature=0.5)
            text = (r.choices[0].message.content or "").strip()
            return text or local_synthesis(seed)
        except Exception:
            return local_synthesis(seed)
