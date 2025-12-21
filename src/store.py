from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

DB_PATH = Path("data/newsletter.db")


@dataclass
class SeenItem:
    url: str
    url_hash: str
    first_seen_utc: str


def ensure_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_urls (
                url_hash TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                first_seen_utc TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_runs (
                run_date TEXT PRIMARY KEY,
                sent_utc TEXT NOT NULL
            )
            """
        )
        conn.commit()


def hash_url(url: str) -> str:
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()


def mark_seen(urls: list[str]) -> None:
    ensure_db()
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        for u in urls:
            h = hash_url(u)
            sql = (
                "INSERT OR IGNORE INTO seen_urls (url_hash, url, first_seen_utc) "
                "VALUES (?, ?, ?)"
            )
            conn.execute(sql, (h, u, now))
        conn.commit()


def is_seen(url: str) -> bool:
    ensure_db()
    h = hash_url(url)
    with sqlite3.connect(DB_PATH) as conn:
        row = (
            conn.execute("SELECT 1 FROM seen_urls WHERE url_hash = ?", (h,))
            .fetchone()
        )
        return row is not None


def already_sent_today(run_date: date) -> bool:
    ensure_db()
    key = run_date.isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        row = (
            conn.execute("SELECT 1 FROM sent_runs WHERE run_date = ?", (key,))
            .fetchone()
        )
        return row is not None


def mark_sent_today(run_date: date) -> None:
    ensure_db()
    key = run_date.isoformat()
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sent_runs (run_date, sent_utc) VALUES (?, ?)",
            (key, now),
        )
        conn.commit()
