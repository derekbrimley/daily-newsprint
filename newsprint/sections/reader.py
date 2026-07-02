"""Today's long read, picked from your Readwise Reader queue.

Requires READWISE_TOKEN (get one at https://readwise.io/access_token).
Inspired by Printernet: one saved article gets "printed" in each edition,
and can optionally be archived afterward so the queue actually shrinks.
"""

import os
import random
import re
from urllib.parse import urlparse

import requests

API = "https://readwise.io/api/v3"


def _headers() -> dict:
    token = os.environ.get("READWISE_TOKEN")
    if not token:
        raise RuntimeError("READWISE_TOKEN not set (see README: Readwise Reader setup)")
    return {"Authorization": f"Token {token}"}


def _pick(docs: list[dict], strategy: str) -> dict:
    docs = sorted(docs, key=lambda d: d.get("created_at") or "")
    if strategy == "random":
        return random.choice(docs)
    if strategy == "newest":
        return docs[-1]
    return docs[0]  # oldest — clear the backlog first


def fetch(config: dict) -> dict:
    cfg = config["sections"]["reader"]
    headers = _headers()

    resp = requests.get(
        f"{API}/list/",
        headers=headers,
        params={"location": cfg.get("location", "later"), "category": "article"},
        timeout=30,
    )
    resp.raise_for_status()
    docs = [d for d in resp.json().get("results", []) if d.get("title")]
    if not docs:
        return {"article": None}

    chosen = _pick(docs, cfg.get("strategy", "oldest"))

    # Fetch full HTML content for just the chosen document.
    resp = requests.get(
        f"{API}/list/",
        headers=headers,
        params={"id": chosen["id"], "withHtmlContent": "true"},
        timeout=30,
    )
    resp.raise_for_status()
    full = resp.json()["results"][0]

    html_content = full.get("html_content") or ""
    html_content = re.sub(r"<script\b.*?</script>", "", html_content,
                          flags=re.DOTALL | re.IGNORECASE)

    word_count = full.get("word_count") or len(re.findall(r"\w+", html_content))
    url = full.get("source_url") or full.get("url") or ""

    if cfg.get("archive_after_print"):
        requests.patch(
            f"{API}/update/{chosen['id']}/",
            headers=headers,
            json={"location": "archive"},
            timeout=30,
        )

    return {"article": {
        "id": chosen["id"],
        "title": full.get("title", "Untitled"),
        "author": full.get("author") or "",
        "site": urlparse(url).netloc.removeprefix("www.") if url else "",
        "url": url,
        "summary": (full.get("summary") or "")[:400],
        "word_count": word_count,
        "reading_minutes": max(1, round(word_count / 230)),
        "html_content": html_content,
    }}
