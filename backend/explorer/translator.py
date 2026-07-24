"""
翻譯模組 - 使用 Google 翻譯將外部情報翻譯為繁體中文
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_cache_path = Path(__file__).resolve().parents[2] / "data" / "translate_cache.json"


def _load_cache() -> Dict[str, Dict[str, str]]:
    try:
        if _cache_path.exists():
            return json.loads(_cache_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_cache(cache: Dict[str, Dict[str, str]]) -> None:
    try:
        _cache_path.parent.mkdir(parents=True, exist_ok=True)
        _cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _translate_with_google(text: str) -> str:
    if not text or not text.strip():
        return text

    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="auto", target="zh-TW").translate(text)
    except Exception:
        return text


def translate_item(item: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(item, dict):
        return item

    title = (item.get("title") or "").strip()
    summary = (item.get("summary") or "").strip()
    source = (item.get("source") or "").strip()

    cache = _load_cache()
    cache_key = f"{source}:{title[:80]}"

    if cache_key in cache:
        cached = cache[cache_key]
        return {
            **item,
            "title": cached.get("title", title),
            "summary": cached.get("summary", summary),
            "translated": True,
        }

    translated_title = _translate_with_google(title)
    translated_summary = _translate_with_google(summary)

    result = {
        **item,
        "title": translated_title or title,
        "summary": translated_summary or summary,
        "translated": True,
    }

    cache[cache_key] = {
        "title": result["title"],
        "summary": result["summary"],
    }
    _save_cache(cache)
    return result


def translate_briefing(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data

    items = data.get("項目", data.get("items", []))
    if not isinstance(items, list):
        return data

    translated_items = [translate_item(item) for item in items]

    result = {**data}
    result["項目"] = translated_items
    if "items" in result:
        result["items"] = translated_items
    result["已翻譯"] = True
    return result
