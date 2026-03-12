"""Database layer for site monitor — sites, seen items, and alert log."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

DB_PATH = Path("data/monitor.db")


@contextmanager
def _conn() -> Generator[sqlite3.Connection, None, None]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        yield conn


def ensure_db() -> None:
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sites (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                url         TEXT    NOT NULL,
                type        TEXT    NOT NULL DEFAULT 'html',  -- 'rss' | 'html'
                css_selector TEXT,                            -- optional CSS selector for html mode
                enabled     INTEGER NOT NULL DEFAULT 1,
                last_checked TEXT,
                last_snapshot TEXT,                           -- hash or newest-item URL
                created_utc  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS seen_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id     INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
                item_key    TEXT    NOT NULL,                 -- url or content hash
                first_seen  TEXT    NOT NULL,
                UNIQUE(site_id, item_key)
            );

            CREATE TABLE IF NOT EXISTS alert_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id     INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
                site_name   TEXT    NOT NULL,
                item_url    TEXT,
                item_title  TEXT,
                sent_utc    TEXT    NOT NULL,
                sms_sid     TEXT
            );
            """
        )
        conn.commit()


# ── Sites ──────────────────────────────────────────────────────────────────

def add_site(name: str, url: str, site_type: str, css_selector: str | None) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO sites (name, url, type, css_selector, created_utc) VALUES (?,?,?,?,?)",
            (name, url, site_type, css_selector or None, now),
        )
        conn.commit()
        return cur.lastrowid  # type: ignore[return-value]


def list_sites() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM sites ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def get_site(site_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM sites WHERE id=?", (site_id,)).fetchone()
        return dict(row) if row else None


def update_site(site_id: int, name: str, url: str, site_type: str, css_selector: str | None) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE sites SET name=?, url=?, type=?, css_selector=? WHERE id=?",
            (name, url, site_type, css_selector or None, site_id),
        )
        conn.commit()


def toggle_site(site_id: int, enabled: bool) -> None:
    with _conn() as conn:
        conn.execute("UPDATE sites SET enabled=? WHERE id=?", (int(enabled), site_id))
        conn.commit()


def delete_site(site_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM sites WHERE id=?", (site_id,))
        conn.commit()


def update_snapshot(site_id: int, snapshot: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute(
            "UPDATE sites SET last_checked=?, last_snapshot=? WHERE id=?",
            (now, snapshot, site_id),
        )
        conn.commit()


# ── Seen items ─────────────────────────────────────────────────────────────

def is_new_item(site_id: int, item_key: str) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM seen_items WHERE site_id=? AND item_key=?",
            (site_id, item_key),
        ).fetchone()
        return row is None


def mark_seen(site_id: int, item_key: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_items (site_id, item_key, first_seen) VALUES (?,?,?)",
            (site_id, item_key, now),
        )
        conn.commit()


# ── Alert log ──────────────────────────────────────────────────────────────

def log_alert(
    site_id: int,
    site_name: str,
    item_url: str | None,
    item_title: str | None,
    sms_sid: str | None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO alert_log (site_id, site_name, item_url, item_title, sent_utc, sms_sid) VALUES (?,?,?,?,?,?)",
            (site_id, site_name, item_url, item_title, now, sms_sid),
        )
        conn.commit()


def list_alerts(limit: int = 50) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM alert_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
