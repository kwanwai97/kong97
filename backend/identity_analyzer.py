"""
Identity Analyzer v2 - deeper blind spot detection.
Uses decisions, daily logs, facts to compute:
- repeated failures / regret patterns
- overconfidence / underconfidence
- procrastination / open-loop ratio
- emotional loops
- missing categories
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from collections import Counter

from backend import identity as identity_module
from datetime import datetime, timedelta


def _texts(docs: List[Dict[str, Any]], keys=("text", "content")) -> List[str]:
    out: List[str] = []
    for d in docs:
        parts: List[str] = []
        for k in keys:
            v = d.get(k, "")
            if v is None:
                continue
            if isinstance(v, list):
                parts.extend([str(x) for x in v if x not in (None, "")])
            else:
                parts.append(str(v))
        t = " ".join(parts)
        if t.strip():
            out.append(t.strip())
    return out


def analyze_blindspots(user_id: str, days: int = 30) -> List[Dict[str, Any]]:
    身份層 = identity_module.IdentityLayer()
    decisions = 身份層.list_decisions(user_id, limit=500)
    logs = 身份層.get_daily_log(user_id, days=days)
    facts = 身份層.get_user_facts(user_id, limit=500)
    signals: List[Dict[str, Any]] = []

    # Topic repetition
    recent = [d for d in reversed(decisions) if d][:50]
    topic_counts = Counter((d.get("topic") or d.get("choice") or "").strip() for d in recent)
    repeated = [k for k, v in topic_counts.items() if k and v > 2]
    if repeated:
        signals.append({
            "pattern": "近期決策主題/選項過度重複，可能固化",
            "evidence": repeated[:5],
            "severity": "medium" if len(repeated) <= 3 else "high",
            "suggestion": "嘗試新選項或限制重複次數"
        })

    # Open-loop ratio
    with_outcome = sum(1 for d in decisions if str(d.get("outcome", "") or "").strip() not in ("", "無"))
    ratio = with_outcome / max(len(decisions), 1)
    if len(decisions) > 5 and ratio < 0.25:
        signals.append({
            "pattern": "決策完成率低，存在拖延/未結案傾向",
            "evidence": [f"decisions={len(decisions)}", f"outcomes={with_outcome}", f"ratio={ratio:.2f}"],
            "severity": "high",
            "suggestion": "每週固定回填成果，減少 open loop"
        })

    # Regret language
    日誌字串 = " ".join(_texts(logs, keys=("entries",)))
    keywords = ["後悔", "損失", "唔該", "唔好", "ERROR", "失敗", "嘥咗", "韋"]
    regret_hits = [k for k in keywords if k in 日誌字串]
    if regret_hits:
        signals.append({
            "pattern": "日誌出現後悔/損失詞頻",
            "evidence": regret_hits[:6],
            "severity": "medium",
            "suggestion": "把 regret 轉為可學習現象：紀錄觸發條件"
        })

    # Domain depth
    topic_diversity = len(set((d.get("topic") or "").strip() for d in recent)) if recent else 0
    if topic_diversity < 3 and len(recent) > 10:
        signals.append({
            "pattern": "決策領域過於集中，可能忽略其他視角",
            "evidence": [f"unique_topics={topic_diversity}", f"recent={len(recent)}"],
            "severity": "medium",
            "suggestion": "定期加入跨領域決策，避免 narrow framing"
        })

    # Fact completeness
    categories = Counter(str(f.get("category", "") or "") for f in facts)
    missing_core = [c for c in ["bio", "pref", "constraint", "goal"] if categories.get(c, 0) < 1]
    if missing_core:
        signals.append({
            "pattern": "身份事實庫不完整，缺少必要分類",
            "evidence": {"missing": missing_core, "current": dict(categories)},
            "severity": "low",
            "suggestion": "先填 bio/pref/constraint，作為推薦基礎"
        })

    if not signals:
        signals.append({
            "pattern": "尚無明顯盲點訊號",
            "evidence": [],
            "severity": "low",
            "suggestion": "繼續記錄決策、日誌、成果"
        })

    return signals
