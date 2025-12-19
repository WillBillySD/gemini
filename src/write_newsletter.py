from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI

from .collect import Story
from .prompts import SYSTEM_PROMPT, WRITER_PROMPT_TEMPLATE


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def _render_templates(subject: str, sections: dict) -> tuple[str, str]:
    html_t = env.get_template("newsletter.html.j2")
    txt_t = env.get_template("newsletter.txt.j2")
    html = html_t.render(subject=subject, **sections)
    text = txt_t.render(subject=subject, **sections)
    return html, text


def write_newsletter(openai_api_key: str, stories: list[Story]) -> dict:
    client = OpenAI(api_key=openai_api_key)

    date_str = datetime.now().strftime("%B %d, %Y")
    stories_json = json.dumps([asdict(s) for s in stories], ensure_ascii=False, indent=2)

    user_prompt = WRITER_PROMPT_TEMPLATE.format(date_str=date_str, stories_json=stories_json)

    # Request the model to output JSON only.
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned empty content")
    data = json.loads(content)

    # If model didn't provide bodies, fall back to template rendering (unlikely, but safe).
    if not data.get("html_body") or not data.get("text_body"):
        sections = {
            "date_str": date_str,
            "top_headlines": data.get("top_headlines", []),
            "stories": [asdict(s) for s in stories],
            "client_insight": "",
        }
        html, text = _render_templates(data.get("subject", f"AI Daily Brief — {date_str}"), sections)
        data["html_body"] = html
        data["text_body"] = text

    return data
