Purpose
This file gives AI coding agents the minimal, actionable knowledge to be productive in this repository: the high-level architecture, key workflows, conventions, and concrete file examples to reference.

**Overview**
- **What:** "AI Daily Brief" — an automated daily newsletter pipeline that collects RSS items, filters/ranks them, generates an HTML/text newsletter via OpenAI, and emails it via SendGrid.
- **Run:** The Python entrypoint is `python -m src.main`.

**How to run locally**
- Create a virtualenv and install: `pip install -r requirements.txt`.
- Copy `.env.example` → `.env` and set `OPENAI_API_KEY` and `SENDGRID_API_KEY` (and optionally `FEED_URLS`, `TOP_N`, `MIN_SCORE`). See `src/config.py` for exact env names.
- Run: `python -m src.main` (the script handles idempotency and will skip if already sent today).

**High-level architecture / data flow**
- Collection: `src/collect.py` reads feeds listed in `src/feeds.py` using `feedparser` and returns `Story` dataclass instances.
- Dedup + Seen: `src/main.py` calls `_dedupe_new` and `src/store.py` to avoid re-sending URLs already in the SQLite DB (`data/newsletter.db`).
- Ranking/filtering: `src/rank.py` scores stories using explicit keyword lists and returns top-N above `MIN_SCORE`.
- Generation: `src/write_newsletter.py` calls OpenAI (model `gpt-4o-mini`) with `SYSTEM_PROMPT`/`WRITER_PROMPT_TEMPLATE` from `src/prompts.py`. The model is asked to output JSON; the code falls back to Jinja templates in `templates/` if the model omits bodies.
- Sending: `src/send_email.py` posts to the SendGrid REST API using `requests`.
- Persistence: `src/store.py` manages `seen_urls` and `sent_runs` tables and creates the DB if missing (`ensure_db`).

**Project-specific conventions & patterns**
- `Story` is a small dataclass defined in `src/collect.py` (fields: `title`, `url`, `source`, `published`, `snippet`). Use `asdict()` when serializing for prompts.
- Keyword scoring instead of embeddings: `src/rank.py` uses hardcoded term lists (`AI_TERMS`, `HOSTING_TERMS`, `MARKETING_TERMS`) and a `NEGATIVE_HINTS` filter — follow this pattern when changing ranking logic.
- Idempotency: The pipeline records daily runs in `sent_runs` and marks seen URLs via SHA-256 hashes (`hash_url`) in `seen_urls`. Respect this flow when modifying send logic.
- Template fallback: The generator expects the model to return `html_body` and `text_body` JSON keys. If missing, `write_newsletter` will render Jinja templates from `templates/newsletter.html.j2` and `templates/newsletter.txt.j2`.
- External model contract: `write_newsletter` requests a JSON object; changing the model or `response_format` requires updating parsing logic and possibly the prompt in `src/prompts.py`.

**Key files to inspect for changes**
- Entrypoint: `src/main.py` — orchestrates the whole pipeline and shows expected order of operations.
- Collector: `src/collect.py` and `src/feeds.py` — adding feeds or changing parsing happens here.
- Ranker: `src/rank.py` — scoring logic and thresholds (`MIN_SCORE`, `TOP_N`) are applied here.
- Generator: `src/write_newsletter.py`, `src/prompts.py`, and templates in `templates/` — modify together.
- Persistence: `src/store.py` — DB path is `data/newsletter.db` and schema is created automatically.
- Sender: `src/send_email.py` — SendGrid integration; errors raise RuntimeError on non-2xx responses.

**External integrations and environment**
- OpenAI: API key via `OPENAI_API_KEY`; `openai.OpenAI` client is used and model set to `gpt-4o-mini` in `src/write_newsletter.py`.
- SendGrid: API key via `SENDGRID_API_KEY`. `src/send_email.py` builds a JSON mail payload and sends to `https://api.sendgrid.com/v3/mail/send`.
- SQLite DB at `data/newsletter.db` (created lazily by `src/store.py`).

**Debugging tips / common edits**
- To reproduce a run locally and see output: set env vars, run `python -m src.main`, and inspect printed result and `data/newsletter.db`.
- To test generation without sending: temporarily stub `src/send_email.send_via_sendgrid` to a no-op or log.
- If OpenAI returns malformed JSON, `write_newsletter` will raise on `json.loads`; check the raw `resp.choices[0].message.content` for debugging.
- When changing templates, keep keys used by the fallback in `write_newsletter` (`top_headlines`, `stories`, `client_insight`, `date_str`).

**Safety & change notes for AI agents**
- Avoid adding new required env vars without updating `README.md` and `.env.example`.
- Do not change the idempotency order: marking sent/seen happens after successful send to avoid skipping when send fails.
- When modifying ranking thresholds or term lists, update defaults in `src/config.py` and document impact on `TOP_N`/`MIN_SCORE`.

Questions / Next steps
- If anything important is missing (CI, tests, other deployment hooks), tell me which area to expand and I'll update this file.
