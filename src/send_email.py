from __future__ import annotations

import json

import requests


def send_via_sendgrid(
    sendgrid_api_key: str,
    from_name: str,
    from_email: str,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> None:
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {sendgrid_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email, "name": from_name},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text_body},
            {"type": "text/html", "value": html_body},
        ],
    }

    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
    if r.status_code >= 300:
        raise RuntimeError(f"SendGrid error {r.status_code}: {r.text}")
