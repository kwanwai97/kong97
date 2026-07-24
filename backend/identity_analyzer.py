"""
IdentityAnalyzer - 使用用户的决策与日志生成盲点信号。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend import identity as identity_module
from datetime import datetime


def analyze_blindspots(user_id: str, days: int = 30) -> List[Dict[str, Any]]:
    身份層 = identity_module.IdentityLayer()
    decisions = 身份層.list_decisions(user_id, limit=200)
    logs = 身份層.get_daily_log(user_id, days=days)
    facts = 身份層.get_user_facts(user_id, limit=200)
    決策主旨 = [ (d.get("topic") or d.get("choice") or "") for d in decisions ]
    outcomes = [ d for d in decisions if d.get("outcome") ]
    主旨無結果 = [d for d in decisions if d.get("outcome") in (None, "", "無") or ("" if d.get("outcome") is None else False)]
    日誌字串 = " ".join(
        " ".join((row.get("entries") or [])) for row in logs
    )
    結果: List[Dict[str, Any]] = []
    決策不足 = any(k in " ".join(決策主旨) for k in ["投機","高槓桿","all-in","高風險"]) and len(decisions) < 3
    if 決策不足:
        結果.append({
            "pattern": "高風險偏好但決策樣本不足，可能決策偏頗",
            "evidence": ["決策中包含高風險詞彙", f"decisions={len(decisions)}"],
            "severity": "high",
        })
    recent = [d for d in reversed(decisions) if d][:20]
    repeated = []
    topics_seen = {}
    for d in recent:
        t = d.get("topic", "")
        topics_seen[t] = topics_seen.get(t, 0) + 1
        if topics_seen[t] > 2 and t not in repeated:
            repeated.append(t)
    if repeated:
        結果.append({
            "pattern": "近期主題重複，可能有固化風險",
            "evidence": repeated,
            "severity": "medium",
        })
    if len(outcomes) > 0 and len(decisions) > 5 and (len(outcomes) / len(decisions)) < 0.2:
        結果.append({
            "pattern": "決策完成率低，存在拖延或未結案傾向",
            "evidence": [f"outcomes={len(outcomes)}", f"decisions={len(decisions)}"],
            "severity": "medium",
        })
    if "後悔" in 日誌字串 or "損失" in 日誌字串:
        結果.append({
            "pattern": "日誌出現情緒詞，可能存在情緒迴圈",
            "evidence": ["出現關鍵詞：後悔/損失"],
            "severity": "medium",
        })
    if not 結果:
        結果.append({
            "pattern": "暫無明顯盲點訊號",
            "evidence": [],
            "severity": "low",
        })
    return 結果
