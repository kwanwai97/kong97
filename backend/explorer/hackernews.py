"""
Hacker News top stories fetcher - real JSON API
"""
from __future__ import annotations

from typing import List

import httpx


class HackerNewsFetcher:
    URL = "https://hacker-news.firebaseio.com/v0/topstories.json"

    def __init__(self, limit: int = 5, timeout: float = 20.0):
        self.limit = limit
        self.timeout = timeout

    def fetch(self) -> List[dict]:
        headers = {"user-agent": "digital-twin/2.0"}
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as c:
            r = c.get(self.URL, headers=headers)
            r.raise_for_status()
            ids = r.json()[: self.limit]
        items: List[dict] = []
        for item_id in ids:
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True) as c:
                    rr = c.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", headers=headers)
                    rr.raise_for_status()
                    data = rr.json() or {}
                title = data.get("title") or ""
                link = data.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
                if title:
                    items.append({"title": title, "link": link, "summary": data.get("by", ""), "published": "", "source": "hackernews"})
            except Exception:
                continue
        return items
