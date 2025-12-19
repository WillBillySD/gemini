from __future__ import annotations

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


def collect_from_feeds(feed_urls: list[str], max_per_feed: int = 15) -> list[Story]:
    stories: list[Story] = []
    for feed_url in feed_urls:
        d = feedparser.parse(feed_url)
        source = (d.feed.get("title") if hasattr(d, "feed") else None) or feed_url
        entries = getattr(d, "entries", [])[:max_per_feed]
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
