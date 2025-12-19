from __future__ import annotations

import re

from .collect import Story


# Lightweight keyword-based relevance scoring.
# (You can later replace with embeddings or a classifier.)
AI_TERMS = [
    "ai", "artificial intelligence", "llm", "chatgpt", "gpt", "anthropic", "claude",
    "openai", "gemini", "copilot", "model", "inference", "rag", "agents"
]
HOSTING_TERMS = [
    "hosting", "cloud", "aws", "azure", "gcp", "google cloud", "cdn", "edge",
    "kubernetes", "k8s", "vps", "server", "datacenter", "infrastructure", "devops",
    "security", "ddos", "waf", "load balancer"
]
MARKETING_TERMS = [
    "marketing", "seo", "search", "content", "ads", "ppc", "conversion", "landing page",
    "email", "crm", "automation", "analytics", "growth", "brand"
]

NEGATIVE_HINTS = [
    "sports", "celebrity", "gossip", "horoscope", "recipe", "coupon"
]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def score_story(story: Story) -> float:
    text = _norm(" ".join([story.title, story.snippet or "", story.source]))
    if any(n in text for n in NEGATIVE_HINTS):
        return 0.0

    ai = sum(1 for t in AI_TERMS if t in text)
    host = sum(1 for t in HOSTING_TERMS if t in text)
    mkt = sum(1 for t in MARKETING_TERMS if t in text)

    # Encourage cross-domain relevance.
    domain_hits = sum(1 for v in (ai, host, mkt) if v > 0)

    raw = (ai * 1.2) + (host * 1.0) + (mkt * 1.0) + (domain_hits * 1.5)
    # Normalize-ish to 0..1 range with a soft cap
    return max(0.0, min(1.0, raw / 10.0))


def rank_and_filter(stories: list[Story], min_score: float, top_n: int) -> list[tuple[Story, float]]:
    scored = [(s, score_story(s)) for s in stories]
    scored = [x for x in scored if x[1] >= min_score]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]
