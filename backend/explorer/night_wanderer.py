"""
Night Wanderer - 夜間巡邏 / 自主探索（真實 arXiv + GitHub Trending + Hacker News）
"""
from __future__ import annotations

import datetime
from typing import Iterable, List, Dict, Any

from backend.safety.human_in_the_loop import HumanInTheLoop
from backend.explorer.arxiv import ArxivFetcher
from backend.explorer.github import GitHubTrendingFetcher
from backend.explorer.hackernews import HackerNewsFetcher


class NightWanderer:
    def __init__(self, timeout: float = 20.0, max_results: int = 4) -> None:
        self.timeout = timeout
        self.max_results = max_results
        self._approver = HumanInTheLoop()

    def crawl(self, sources: Iterable[str]) -> List[Dict[str, Any]]:
        src_list = [s.strip().lower() for s in sources]
        items: List[Dict[str, Any]] = []

        if "arxiv" in src_list:
            if self._approver.approve({"標籤": "crawl:arxiv"}).get("已核准"):
                try:
                    items.extend(ArxivFetcher(timeout=self.timeout).fetch()[: self.max_results])
                except Exception as exc:
                    items.append({"title": f"arxiv 爬取失敗", "link": "", "summary": str(exc), "source": "arxiv"})

        if "github" in src_list or "github trending" in src_list:
            if self._approver.approve({"標籤": "crawl:github"}).get("已核准"):
                try:
                    items.extend(GitHubTrendingFetcher(timeout=self.timeout).fetch()[: self.max_results])
                except Exception as exc:
                    items.append({"title": f"github 爬取失敗", "link": "", "summary": str(exc), "source": "github"})

        if "hackernews" in src_list or "hn" in src_list:
            if self._approver.approve({"標籤": "crawl:hackernews"}).get("已核准"):
                try:
                    items.extend(HackerNewsFetcher(limit=self.max_results, timeout=self.timeout).fetch()[: self.max_results])
                except Exception as exc:
                    items.append({"title": f"hackernews 爬取失敗", "link": "", "summary": str(exc), "source": "hackernews"})

        if not items:
            items.append({"title": "未選擇來源", "link": "", "summary": "請提供至少一個有效 source: arxiv, github, hackernews", "source": "system"})

        return items

    def summarize(self, items: List[Dict[str, Any]]) -> str:
        lines = []
        for it in items[:8]:
            title = it.get("title", it.get("標題", "untitled")) if isinstance(it, dict) else str(it)
            src = it.get("source", it.get("來源", "unknown")) if isinstance(it, dict) else "text"
            lines.append(f"[{src}] {title}")
        joined = "; ".join(lines)
        return f"[摘要 {datetime.datetime.utcnow().isoformat()}Z] 共 {len(items)} 則：{joined}"
