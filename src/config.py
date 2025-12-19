from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    return float(v) if v is not None else default


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    return int(v) if v is not None else default


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    sendgrid_api_key: str

    from_name: str
    from_email: str
    to_email: str

    top_n: int
    min_score: float

    feed_urls_override: list[str]


def load_settings() -> Settings:
    feed_override = os.getenv("FEED_URLS", "").strip()
    feed_urls = [u.strip() for u in feed_override.split(",") if u.strip()] if feed_override else []

    return Settings(
        openai_api_key=_env("OPENAI_API_KEY"),
        sendgrid_api_key=_env("SENDGRID_API_KEY"),
        from_name=_env("FROM_NAME", "Matt Gage Digital"),
        from_email=_env("FROM_EMAIL", "matt@mattgage.net"),
        to_email=_env("TO_EMAIL", "matt@mattgage.net"),
        top_n=_env_int("TOP_N", 8),
        min_score=_env_float("MIN_SCORE", 0.35),
        feed_urls_override=feed_urls,
    )
