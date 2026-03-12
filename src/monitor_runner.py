"""Core check loop — runs on schedule and on-demand from the web UI."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from . import monitor_db as db
from .monitor_check import fetch_items
from .monitor_sms import build_alert_body, send_sms

log = logging.getLogger(__name__)


def run_checks(site_id: int | None = None) -> dict:
    """
    Check all enabled sites (or one specific site if site_id given).
    Returns a summary dict.
    """
    db.ensure_db()

    sites = db.list_sites()
    if site_id is not None:
        sites = [s for s in sites if s["id"] == site_id]

    total_alerts = 0
    errors: list[str] = []

    for site in sites:
        if not site["enabled"] and site_id is None:
            continue
        try:
            alerts = _check_site(site)
            total_alerts += alerts
        except Exception as exc:
            log.exception("Unexpected error checking site %s", site["name"])
            errors.append(f"{site['name']}: {exc}")

    return {
        "checked": len(sites),
        "alerts_sent": total_alerts,
        "errors": errors,
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }


def _check_site(site: dict) -> int:
    """Check a single site, send SMS for new items. Returns count of alerts sent."""
    site_id = site["id"]
    site_name = site["name"]
    site_type = (site.get("type") or "html").lower()

    log.info("Checking %s (%s) — %s", site_name, site_type, site["url"])

    items = fetch_items(site)
    if not items:
        log.info("No items returned for %s", site_name)
        db.update_snapshot(site_id, "")
        return 0

    alerts_sent = 0
    new_keys: list[str] = []

    for item in items:
        if db.is_new_item(site_id, item.key):
            new_keys.append(item.key)

            # For HTML pages the "item" is just a changed hash — don't flood SMS;
            # send one alert per check cycle.
            if site_type == "html" and alerts_sent > 0:
                continue

            body = build_alert_body(site_name, item.title, item.url)
            sms_sid = send_sms(body)
            db.log_alert(site_id, site_name, item.url, item.title, sms_sid)
            alerts_sent += 1

    # Mark all new keys as seen after sending alerts
    for key in new_keys:
        db.mark_seen(site_id, key)

    # Update snapshot with latest key
    db.update_snapshot(site_id, items[0].key)

    if new_keys:
        log.info("%d new item(s) found for %s", len(new_keys), site_name)
    return alerts_sent
