"""SMS alert sending via Twilio."""
from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)


def send_sms(body: str) -> str | None:
    """
    Send an SMS via Twilio.  Returns the Twilio message SID on success,
    or None if credentials are missing / sending fails.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_FROM_NUMBER", "")
    to_number = os.getenv("ALERT_TO_NUMBER", "")

    if not all([account_sid, auth_token, from_number, to_number]):
        log.warning(
            "Twilio credentials incomplete — skipping SMS. "
            "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
            "TWILIO_FROM_NUMBER, ALERT_TO_NUMBER in your .env"
        )
        return None

    try:
        from twilio.rest import Client  # lazy import so app boots without Twilio creds

        client = Client(account_sid, auth_token)
        msg = client.messages.create(body=body, from_=from_number, to=to_number)
        log.info("SMS sent: %s", msg.sid)
        return msg.sid
    except Exception as exc:
        log.error("Failed to send SMS: %s", exc)
        return None


def build_alert_body(site_name: str, item_title: str | None, item_url: str | None) -> str:
    lines = [f"New post on {site_name}!"]
    if item_title:
        lines.append(item_title)
    if item_url:
        lines.append(item_url)
    return "\n".join(lines)
