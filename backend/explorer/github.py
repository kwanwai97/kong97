"""
Real GitHub Trending fetcher - 真實 GitHub Trending 每日摘要
"""
from __future__ import annotations

import re
from typing import List

import httpx


class GitHubTrendingFetcher:
    URL = "https://github.com/trending"
    HEADERS = {"user-agent": "digital-twin/2.0 (+https://example.com)"}

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def fetch(self, since: str = "daily") -> List[dict]:
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as c:
            r = c.get(self.URL, params={"since": since}, headers=self.HEADERS)
            r.raise_for_status()
            html = r.text
        return self._parse(html)

    def _parse(self, html: str) -> List[dict]:
        items: List[dict] = []
        for row in re.findall(r'<article[\s\S]*?class="[^"]*Box-row[^"]*?"[\s\S]*?</article>', html, re.I):
            title = (self._h2(row) or self._h1(row)).strip()
            desc = self._desc(row)
            link_m = re.search(r'href="(/[^"]+)"', row)
            link = f"https://github.com{link_m.group(1)}" if link_m else ""
            if title:
                items.append({"title": title, "link": link, "summary": (desc or "").strip(), "source": "github"})
        return items

    @staticmethod
    def _h2(block: str) -> str:
        m = re.search(r"<h2[^>]*?>\s*<a[^>]+>\s*(?:<span[^>]*?>)?\s*([\s\S]*?)\s*(?:</span>)?\s*</a>", block, re.I)
        if not m:
            return ""
        s = m.group(1).strip()
        s = re.sub(r"<[^>]+>", "", s)
        return " ".join(s.split())

    @staticmethod
    def _h1(block: str) -> str:
        m = re.search(r"<h1[^>]*?>\s*<a[^>]+>\s*([\s\S]*?)\s*</a>", block, re.I)
        if not m:
            return ""
        s = m.group(1).strip()
        s = re.sub(r"<[^>]+>", "", s)
        return " ".join(s.split())

    @staticmethod
    def _desc(block: str) -> str:
        m = re.search(r"<p[\s\S]*?class=\"[^\"]*col-9[^\"]*?\"[\s\S]*?>\s*([\s\S]*?)\s*</p>", block, re.I)
        if not m:
            return ""
        s = m.group(1).strip()
        s = re.sub(r"<[^>]+>", "", s)
        return " ".join(s.split())
