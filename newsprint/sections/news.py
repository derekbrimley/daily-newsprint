"""Headlines from RSS/Atom feeds (no API key required)."""

import html
import re
import xml.etree.ElementTree as ET

import requests

ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)  # strip embedded HTML from summaries
    return html.unescape(text).strip()


def _parse_feed(content: bytes, limit: int) -> list[dict]:
    root = ET.fromstring(content)
    items = []

    for item in root.iter("item"):  # RSS 2.0
        items.append({
            "title": _clean(item.findtext("title")),
            "link": (item.findtext("link") or "").strip(),
            "summary": _clean(item.findtext("description"))[:300],
        })
        if len(items) >= limit:
            return items

    if not items:  # Atom
        for entry in root.iter(f"{ATOM_NS}entry"):
            link_el = entry.find(f"{ATOM_NS}link")
            items.append({
                "title": _clean(entry.findtext(f"{ATOM_NS}title")),
                "link": link_el.get("href", "") if link_el is not None else "",
                "summary": _clean(entry.findtext(f"{ATOM_NS}summary"))[:300],
            })
            if len(items) >= limit:
                break

    return items


def fetch(config: dict) -> dict:
    cfg = config["sections"]["news"]
    limit = cfg.get("max_per_feed", 5)
    feeds = []

    for feed in cfg["feeds"]:
        try:
            resp = requests.get(
                feed["url"], timeout=20,
                headers={"User-Agent": "daily-newsprint/0.1"},
            )
            resp.raise_for_status()
            feeds.append({"name": feed["name"], "items": _parse_feed(resp.content, limit)})
        except Exception as exc:  # one bad feed shouldn't kill the section
            feeds.append({"name": feed["name"], "items": [], "error": str(exc)})

    return {"feeds": feeds}
