#!/usr/bin/env python3
"""
Entry point for the Site Monitor web app.

Usage:
    python monitor.py

Environment (copy .env.example to .env and fill in values):
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
    ALERT_TO_NUMBER
    CHECK_INTERVAL_MINUTES  (default 30)
    SECRET_KEY              (any random string)
    PORT                    (default 5000)
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("monitor")

from apscheduler.schedulers.background import BackgroundScheduler
from src.monitor_db import ensure_db
from src.monitor_runner import run_checks
from src.monitor_web import app


def _scheduled_check() -> None:
    log.info("Scheduled check starting…")
    result = run_checks()
    log.info(
        "Scheduled check done — %d site(s) checked, %d alert(s) sent",
        result["checked"],
        result["alerts_sent"],
    )
    if result["errors"]:
        for err in result["errors"]:
            log.warning("Check error: %s", err)


def main() -> None:
    ensure_db()

    interval = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
    port = int(os.getenv("PORT", "5000"))

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(_scheduled_check, "interval", minutes=interval, id="site_check")
    scheduler.start()
    log.info("Scheduler started — checking every %d minute(s)", interval)

    log.info("Starting web UI on http://0.0.0.0:%d", port)
    # use_reloader=False keeps APScheduler from double-starting
    app.run(host="0.0.0.0", port=port, use_reloader=False)


if __name__ == "__main__":
    main()
