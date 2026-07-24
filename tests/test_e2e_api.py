import asyncio
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5678"


def _ok():
    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def get(path):
    if not _ok():
        raise RuntimeError("server not running")
    with urllib.request.urlopen(f"{BASE}{path}", timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def post(path, payload):
    if not _ok():
        raise RuntimeError("server not running")
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))


def test_health():
    assert get("/health").get("狀態") == "正常"


def test_dialectic_returns_three_parts():
    data = post("/dialectic", {"text": "今日恒生指數期貨會點樣？"})
    assert "正方" in data and "反方" in data and "整合結論" in data
    assert data["正方"].startswith("【正方】")
    assert data["整合結論"].startswith("【整合結論】")


def test_briefing_today_has_translated_items():
    data = get("/briefing/today")
    items = data.get("項目", data.get("items", []))
    assert isinstance(items, list) and len(items) >= 1
    translated = (
        all(it.get("translated") or it.get("已翻譯") for it in items)
        or data.get("已翻譯") is True
    )
    assert translated
