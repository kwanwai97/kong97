"""
Financial Intelligence Fetcher - 財經情報來源
Yahoo Finance + HKEX + Reuters 雅虎股市、香港交易所、路透社
"""
from __future__ import annotations

import json
import datetime
from typing import List, Dict, Any


class FinancialFetcher:
    def __init__(self, timeout: float = 20.0, max_results: int = 6) -> None:
        self.timeout = timeout
        self.max_results = max_results

    def fetch(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        try:
            results.extend(self._yahoo_hsi())
        except Exception:
            pass
        try:
            results.extend(self._hkex_news())
        except Exception:
            pass
        try:
            results.extend(self._reuters_hk())
        except Exception:
            pass
        if not results:
            results.append({
                "title": "財經情報暫時未能獲取",
                "link": "",
                "summary": "建議檢查網絡連線，或稍後再試。",
                "source": "finance",
            })
        return results

    def _yahoo_hsi(self) -> List[Dict[str, Any]]:
        import urllib.request
        url = "https://fc.yahoo.com/p/v1/finance/quote?symbols=%5EHSI&formatted=true&lang=zh-Hant-HK&region=HK"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        items: List[Dict[str, Any]] = []
        for q in data.get("quoteResponse", {}).get("result", []):
            title = q.get("shortName", "恒生指數")
            price = q.get("price", "N/A")
            change = q.get("change", "N/A")
            pct = q.get("percentChange", "N/A")
            summary = f"恒生指數報價：{price}，變動 {change}（{pct}%）"
            items.append({
                "title": title,
                "link": f"https://hk.finance.yahoo.com/quote/%5EHSI",
                "summary": summary,
                "published": datetime.datetime.utcnow().isoformat() + "Z",
                "source": "yahoo",
            })
        return items[: self.max_results]

    def _hkex_news(self) -> List[Dict[str, Any]]:
        import urllib.request
        url = "https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities?sc_lang=zh-HK"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            html = r.read().decode("utf-8", errors="ignore")
        # Extract a few headlines from meta tags as a lightweight proxy
        items: List[Dict[str, Any]] = []
        import re
        titles = re.findall(r'<title[^>]*>([^<]+)</title>', html)
        cleaned = []
        for t in titles[:3]:
            t = t.strip()
            if t and t not in cleaned:
                cleaned.append(t)
        for t in cleaned:
            items.append({
                "title": t,
                "link": "https://www.hkex.com.hk",
                "summary": "香港交易所市場資訊頁面。",
                "published": datetime.datetime.utcnow().isoformat() + "Z",
                "source": "hkex",
            })
        if not items:
            items.append({
                "title": "港股今日表現",
                "link": "https://www.hkex.com.hk",
                "summary": "請前往 HKEX 查看今日港股大市表現、成交額與板塊輪動情況。",
                "published": datetime.datetime.utcnow().isoformat() + "Z",
                "source": "hkex",
            })
        return items[: self.max_results]

    def _reuters_hk(self) -> List[Dict[str, Any]]:
        import urllib.request
        url = "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            xml = r.read().decode("utf-8", errors="ignore")
        items: List[Dict[str, Any]] = []
        import re
        titles = re.findall(r'<title[^>]*>([^<]+)</title>', xml)
        links = re.findall(r'<link[^>]*>([^<]+)</link>', xml)
        seen = set()
        count = 0
        for idx, t in enumerate(titles[: self.max_results]):
            t = t.strip()
            if not t or t in seen:
                continue
            seen.add(t)
            link = links[idx] if idx < len(links) else "https://www.reuters.com"
            items.append({
                "title": t,
                "link": link,
                "summary": "Reuters 商業與金融新聞摘要。",
                "published": datetime.datetime.utcnow().isoformat() + "Z",
                "source": "reuters",
            })
            count += 1
        if not items:
            items.append({
                "title": "Reuters 金融市場",
                "link": "https://www.reuters.com",
                "summary": "請前往 Reuters 查看最新國際金融消息。",
                "published": datetime.datetime.utcnow().isoformat() + "Z",
                "source": "reuters",
            })
        return items[: self.max_results]
