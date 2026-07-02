"""Build the morning edition: fetch every enabled section, render, write HTML.

Usage: python -m newsprint.build [--config config.yaml]
"""

import argparse
import json
import pathlib
import sys

import yaml

from . import render, summarize
from .sections import calendar_today, gmail_unread, news, surf, weather

FETCHERS = {
    "weather": weather.fetch,
    "surf": surf.fetch,
    "news": news.fetch,
    "gmail": gmail_unread.fetch,
    "calendar": calendar_today.fetch,
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

    briefing = None
    if config["sections"].get("briefing", {}).get("enabled"):
        print("» asking the editor for a briefing...", flush=True)
        briefing = summarize.write_briefing(sections, config)
        if briefing is None:
            print("  (no Anthropic credentials or call failed — skipping)")

    out_dir = pathlib.Path(config["output"]["directory"])
    out_dir.mkdir(parents=True, exist_ok=True)

    html = render.render(sections, briefing, config)
    (out_dir / "index.html").write_text(html)
    (out_dir / "data.json").write_text(json.dumps(sections, indent=2, default=str))

    print(f"✓ edition printed to {out_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
