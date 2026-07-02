"""Build the morning edition: fetch every enabled section, render, write HTML.

Usage: python -m newsprint.build [--config config.yaml]
"""

import argparse
import json
import pathlib
import sys

import yaml

from . import eink, render, summarize
from .sections import calendar_today, gmail_unread, news, reader, surf, weather

FETCHERS = {
    "weather": weather.fetch,
    "surf": surf.fetch,
    "news": news.fetch,
    "gmail": gmail_unread.fetch,
    "calendar": calendar_today.fetch,
    "reader": reader.fetch,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Print today's edition.")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    config = yaml.safe_load(pathlib.Path(args.config).read_text())

    sections: dict = {}
    for name, fetch in FETCHERS.items():
        if not config["sections"].get(name, {}).get("enabled"):
            continue
        print(f"» fetching {name}...", flush=True)
        try:
            sections[name] = {"data": fetch(config)}
        except Exception as exc:
            print(f"  ! {name} failed: {exc}", file=sys.stderr)
            sections[name] = {"error": str(exc)}

    out_dir = pathlib.Path(config["output"]["directory"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # The long read gets its own page; keep the heavy HTML out of everything else.
    article = (sections.get("reader", {}).get("data") or {}).get("article")
    if article and article.get("html_content"):
        (out_dir / "article.html").write_text(render.render_article(article, config))
        article.pop("html_content")
        print(f"✓ long read printed to {out_dir / 'article.html'}")

    briefing = None
    if config["sections"].get("briefing", {}).get("enabled"):
        print("» asking the editor for a briefing...", flush=True)
        briefing = summarize.write_briefing(sections, config)
        if briefing is None:
            print("  (no Claude CLI or Anthropic credentials — skipping)")

    html = render.render(sections, briefing, config)
    (out_dir / "index.html").write_text(html)
    (out_dir / "data.json").write_text(json.dumps(sections, indent=2, default=str))
    print(f"✓ edition printed to {out_dir / 'index.html'}")

    if config.get("eink", {}).get("enabled"):
        eink_html = eink.build_html(sections, config)
        (out_dir / "eink.html").write_text(eink_html)
        if eink.render_png(eink_html, str(out_dir / "eink.png"), config):
            print(f"✓ e-ink front page rendered to {out_dir / 'eink.png'}")
        else:
            print("  (Playwright not installed — wrote eink.html only; "
                  "pip install playwright && playwright install chromium)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
