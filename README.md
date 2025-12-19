# AI Daily Brief

Daily automated newsletter generator (AI + web hosting + marketing). Collects fresh stories, filters/ranks, writes a client-ready brief with citations (source links), and emails it to you via SendGrid.

## What it does
- Pulls items from curated RSS feeds (AI + hosting/cloud + marketing)
- Filters + ranks by relevance
- Deduplicates (won't resend the same URLs)
- Generates a daily newsletter (HTML + plain text) using OpenAI
- Emails to you (approval mode) via SendGrid
- Stores sent history in SQLite

## Quick start (local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with OPENAI_API_KEY + SENDGRID_API_KEY

python -m src.main
```
