from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass
from datetime import timezone
from dateutil import parser as dateparser
import feedparser


@dataclass
class Story:
    title: str
    url: str
    source: str
    published: str | None
    snippet: str | None


def _parse_published(entry) -> str | None:
    for k in ("published", "updated", "created"):
        if hasattr(entry, k):
            try:
                dt = dateparser.parse(getattr(entry, k))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).isoformat()
            except Exception:
                return None
    return None


def _fetch_feed(feed_url: str, max_per_feed: int) -> list[Story]:
    try:
        d = feedparser.parse(feed_url)
    except Exception:  # pylint: disable=broad-exception-caught
        return []

    source = (d.feed.get("title") if hasattr(d, "feed") else None) or feed_url
    entries = getattr(d, "entries", [])[:max_per_feed]
    stories: list[Story] = []

    for e in entries:
        title = (getattr(e, "title", "") or "").strip()
        link = (getattr(e, "link", "") or "").strip()
        if not title or not link:
            continue
        snippet = (getattr(e, "summary", None) or getattr(e, "description", None) or None)
        if snippet:
            snippet = " ".join(snippet.split())
            snippet = snippet[:600]
        published = _parse_published(e)
        stories.append(Story(title=title, url=link, source=str(source), published=published, snippet=snippet))
    return stories


def collect_from_feeds(feed_urls: list[str], max_per_feed: int = 15) -> list[Story]:
    stories: list[Story] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(feed_urls) or 1)) as executor:
        future_to_url = {executor.submit(_fetch_feed, url, max_per_feed): url for url in feed_urls}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                stories.extend(future.result())
            except Exception:  # pylint: disable=broad-exception-caught
                # If a thread completely fails (rare given inner try/except), ignore
                pass
    return stories
