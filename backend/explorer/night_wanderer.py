"""
Night Wanderer - 夜間巡邏 / 自主探索（真實 arXiv + GitHub Trending + Hacker News）
"""
from __future__ import annotations

import datetime
from typing import Iterable, List

from backend.explorer.arxiv import ArxivFetcher
from backend.explorer.github import GitHubTrendingFetcher
from backend.explorer.hackernews import HackerNewsFetcher
from backend.safety.human_in_the_loop import HumanInTheLoop


hitl = HumanInTheLoop()


class NightWanderer:
    def __init__(self, timeout: float = 20.0, max_results: int = 4) -> None:
        self.timeout = timeout
        self.max_results = max_results

    def crawl(self, sources: Iterable[str]) -> List[dict]:
        src_list = [s.strip().lower() for s in sources]
        items: List[dict] = []

        if "arxiv" in src_list:
            if hitl.approve({"label": "crawl:arxiv"}).get("approved"):
                try:
                    items.extend(ArxivFetcher(timeout=self.timeout).fetch()[: self.max_results])
                except Exception as exc:
                    items.append({"source": "arxiv", "title": "arxiv crawl failed", "summary": str(exc), "link": ""})

        if "github" in src_list:
            if hitl.approve({"label": "crawl:github"}).get("approved"):
                try:
                    items.extend(GitHubTrendingFetcher(timeout=self.timeout).fetch()[: self.max_results])
                except Exception as exc:
                    items.append({"source": "github", "title": "github crawl failed", "summary": str(exc), "link": ""})

        if "hackernews" in src_list or "hn" in src_list:
            if hitl.approve({"label": "crawl:hackernews"}).get("approved"):
                try:
                    items.extend(HackerNewsFetcher(limit=self.max_results, timeout=self.timeout).fetch()[: self.max_results])
                except Exception as exc:
                    items.append({"source": "hackernews", "title": "hackernews crawl failed", "summary": str(exc), "link": ""})

        if not items:
            items.append({"source": "system", "title": "no sources selected", "summary": "請提供至少一個有效 source: arxiv, github, hackernews", "link": ""})

        return items

    def summarize(self, items: List[dict]) -> str:
        lines = []
        for it in items[:8]:
            title = it.get("title", "untitled")
            src = it.get("source", "unknown")
            lines.append(f"[{src}] {title}")
        joined = "; ".join(lines)
        return f"[摘要 {datetime.datetime.utcnow().isoformat()}Z] 共 {len(items)} 則：{joined}"
