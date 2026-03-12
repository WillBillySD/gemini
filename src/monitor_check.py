"""Site-checking logic: RSS/Atom feeds and HTML page monitoring."""
from __future__ import annotations

import hashlib
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SiteMonitorBot/1.0)"}
TIMEOUT = 15  # seconds


@dataclass
class NewItem:
    key: str          # unique key to deduplicate (URL or hash)
    title: str | None
    url: str | None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text(el: ET.Element, tag: str, ns: str = "") -> str:
    child = el.find(f"{{{ns}}}{tag}" if ns else tag)
    return (child.text or "").strip() if child is not None else ""


# ── RSS / Atom ─────────────────────────────────────────────────────────────

def check_rss(url: str) -> list[NewItem]:
    """Fetch and parse an RSS 2.0 or Atom feed; return all items."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as exc:
        log.warning("Feed error for %s: %s", url, exc)
        return []

    # Atom feed
    atom_ns = "http://www.w3.org/2005/Atom"
    if root.tag == f"{{{atom_ns}}}feed" or root.tag.endswith("}feed"):
        return _parse_atom(root, atom_ns)

    # RSS 2.0 / RDF
    return _parse_rss(root)


def _parse_rss(root: ET.Element) -> list[NewItem]:
    items: list[NewItem] = []
    for item in root.iter("item"):
        link  = _text(item, "link")
        guid  = _text(item, "guid") or link
        title = _text(item, "title") or None
        key   = guid or _sha256(ET.tostring(item).decode())
        items.append(NewItem(key=key, title=title, url=link or None))
    return items


def _parse_atom(root: ET.Element, ns: str) -> list[NewItem]:
    items: list[NewItem] = []
    for entry in root.iter(f"{{{ns}}}entry"):
        title_el = entry.find(f"{{{ns}}}title")
        title    = (title_el.text or "").strip() if title_el is not None else None
        link_el  = entry.find(f"{{{ns}}}link")
        link     = (link_el.get("href") or "").strip() if link_el is not None else ""
        id_el    = entry.find(f"{{{ns}}}id")
        item_id  = (id_el.text or "").strip() if id_el is not None else ""
        key      = item_id or link or _sha256(ET.tostring(entry).decode())
        items.append(NewItem(key=key, title=title or None, url=link or None))
    return items


# ── HTML page ──────────────────────────────────────────────────────────────

def check_html(url: str, css_selector: str | None) -> list[NewItem]:
    """
    Fetch the page and return a single NewItem whose key is a hash of the
    targeted content.  If css_selector is given, only that element is hashed;
    otherwise the whole <body> is used.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("HTTP error for %s: %s", url, exc)
        return []

    soup = BeautifulSoup(resp.text, "lxml")

    if css_selector:
        target = soup.select(css_selector)
        content = " ".join(el.get_text(" ", strip=True) for el in target)
    else:
        body = soup.find("body")
        content = body.get_text(" ", strip=True) if body else soup.get_text(" ", strip=True)

    if not content:
        log.warning("No content found at %s (selector=%s)", url, css_selector)
        return []

    key = _sha256(content)
    return [NewItem(key=key, title=None, url=url)]


# ── Dispatcher ─────────────────────────────────────────────────────────────

def fetch_items(site: dict) -> list[NewItem]:
    """Return current items for a site dict from the database."""
    site_type = (site.get("type") or "html").lower()
    url = site["url"]
    selector = site.get("css_selector")

    if site_type == "rss":
        return check_rss(url)
    return check_html(url, selector)
