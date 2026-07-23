"""
Real arXiv fetcher - 真實 arXiv 論文摘要爬蟲
"""
from __future__ import annotations

import datetime
import re
from typing import List
from urllib.parse import quote

import httpx


ENTRY_RE = re.compile(r"<entry>([\s\S]*?)</entry>", re.I)
TITLE_RE = re.compile(r"<title>([\s\S]*?)</title>", re.I)
LINK_RE = re.compile(r"<id>(.*?)</id>", re.I)
SUMMARY_RE = re.compile(r"<summary>([\s\S]*?)</summary>", re.I)
PUBLISHED_RE = re.compile(r"<published>(.*?)</published>", re.I)


class ArxivFetcher:
    BASE = "https://export.arxiv.org/api/query"

    def __init__(self, category: str = "cs.AI", max_results: int = 5, timeout: float = 20.0):
        self.category = category
        self.max_results = max_results
        self.timeout = timeout

    def fetch(self) -> List[dict]:
        query = f"cat:{quote(self.category)}"
        url = (
            f"{self.BASE}?search_query={quote(query)}"
            f"&sortBy=submittedDate&sortOrder=descending&max_results={self.max_results}"
        )
        headers = {"user-agent": "digital-twin/2.0 (+https://example.com)"}
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as c:
            r = c.get(url, headers=headers)
            r.raise_for_status()
            body = r.text
        return self._parse(body)

    def _parse(self, raw: str) -> List[dict]:
        items: List[dict] = []
        for entry in ENTRY_RE.findall(raw):
            title = self._first(TITLE_RE, entry)
            link = self._first(LINK_RE, entry)
            summary = self._first(SUMMARY_RE, entry)
            pub = self._first(PUBLISHED_RE, entry)
            if not title or title.startswith("ArXiv"):
                continue
            items.append({"title": title.strip(), "link": (link or "").strip(), "summary": (summary or "").strip(), "published": (pub or "").strip(), "source": "arxiv"})
        return items

    @staticmethod
    def _first(regex: re.Pattern, text: str) -> str:
        m = regex.search(text)
        return m.group(1).strip() if m else ""
