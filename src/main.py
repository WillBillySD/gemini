from __future__ import annotations

from datetime import date

from .config import load_settings
from .feeds import DEFAULT_FEEDS
from .collect import collect_from_feeds, Story
from .rank import rank_and_filter
from .store import mark_seen, already_sent_today, mark_sent_today, filter_seen_hashes, hash_url
from .write_newsletter import write_newsletter
from .send_email import send_via_sendgrid


def _dedupe_new(stories: list[Story]) -> list[Story]:
    # 1. Dedupe within the current list (by URL)
    unique_candidates: list[Story] = []
    seen_in_batch: set[str] = set()
    for s in stories:
        if s.url not in seen_in_batch:
            unique_candidates.append(s)
            seen_in_batch.add(s.url)

    if not unique_candidates:
        return []

    # 2. Check DB for these candidates in batch
    candidate_hashes = [hash_url(s.url) for s in unique_candidates]
    already_seen_hashes = filter_seen_hashes(candidate_hashes)

    # 3. Filter out those that are in DB
    final_list: list[Story] = []
    for s in unique_candidates:
        if hash_url(s.url) not in already_seen_hashes:
            final_list.append(s)

    return final_list


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
