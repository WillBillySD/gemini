from __future__ import annotations

from datetime import date

from .config import load_settings
from .feeds import DEFAULT_FEEDS
from .collect import collect_from_feeds, Story
from .rank import rank_and_filter
from .store import is_seen, mark_seen, already_sent_today, mark_sent_today
from .write_newsletter import write_newsletter
from .send_email import send_via_sendgrid


def _dedupe_new(stories: list[Story]) -> list[Story]:
    out: list[Story] = []
    seen_urls: set[str] = set()
    for s in stories:
        if s.url in seen_urls:
            continue
        seen_urls.add(s.url)
        if is_seen(s.url):
            continue
        out.append(s)
    return out


def run() -> dict:
    settings = load_settings()
    today = date.today()

    # Prevent double-send if workflow runs twice.
    if already_sent_today(today):
        return {"status": "skipped", "reason": "already_sent_today"}

    feeds = settings.feed_urls_override or DEFAULT_FEEDS

    collected = collect_from_feeds(feeds, max_per_feed=20)
    fresh = _dedupe_new(collected)

    ranked = rank_and_filter(fresh, min_score=settings.min_score, top_n=settings.top_n)
    top_stories = [s for (s, _score) in ranked]

    if not top_stories:
        return {"status": "skipped", "reason": "no_stories_after_filter"}

    newsletter = write_newsletter(settings.openai_api_key, top_stories)

    send_via_sendgrid(
        sendgrid_api_key=settings.sendgrid_api_key,
        from_name=settings.from_name,
        from_email=settings.from_email,
        to_email=settings.to_email,
        subject=newsletter["subject"],
        html_body=newsletter["html_body"],
        text_body=newsletter["text_body"],
    )

    # Mark seen after writing/sending to avoid skipping URLs if send fails.
    mark_seen([s.url for s in top_stories])
    mark_sent_today(today)

    return {
        "status": "sent",
        "subject": newsletter.get("subject"),
        "included_urls": newsletter.get("included_urls", []),
    }


if __name__ == "__main__":
    result = run()
    print(result)
