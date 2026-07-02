"""Render collected section data into a broadsheet-styled HTML page."""

import datetime
from html import escape

CSS = """
:root {
  --paper: #f7f3e8; --ink: #1c1a17; --faint: #6b6357; --rule: #c9bfa8;
  --accent: #8c2f1b;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #e8e2d2; color: var(--ink);
  font-family: Georgia, 'Times New Roman', serif;
  padding: 2rem 1rem;
}
.sheet {
  max-width: 1060px; margin: 0 auto; background: var(--paper);
  padding: 2.5rem 3rem 3rem; box-shadow: 0 2px 24px rgba(0,0,0,.25);
}
.masthead { text-align: center; border-bottom: 4px double var(--ink); padding-bottom: 1rem; }
.masthead h1 {
  font-size: clamp(2.2rem, 7vw, 4.2rem); letter-spacing: .02em;
  font-weight: 900; font-variant: small-caps;
}
.dateline {
  display: flex; justify-content: space-between; gap: 1rem;
  font-size: .8rem; text-transform: uppercase; letter-spacing: .12em;
  border-top: 1px solid var(--ink); margin-top: .8rem; padding-top: .5rem;
  color: var(--faint); flex-wrap: wrap;
}
.briefing {
  border-bottom: 1px solid var(--rule); padding: 1.4rem .5rem;
  font-size: 1.12rem; line-height: 1.65; font-style: italic; text-align: center;
}
.briefing::before { content: "❧ "; color: var(--accent); font-style: normal; }
.columns {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 0 2rem; padding-top: 1.5rem;
}
section { break-inside: avoid; padding-bottom: 1.8rem; }
section h2 {
  font-size: .85rem; text-transform: uppercase; letter-spacing: .18em;
  border-top: 3px solid var(--ink); border-bottom: 1px solid var(--ink);
  padding: .35rem 0; margin-bottom: .9rem;
}
section h2 span { color: var(--accent); }
.bignum { font-size: 3rem; font-weight: 900; line-height: 1; }
.stat-row { display: flex; gap: 1.4rem; align-items: baseline; margin-bottom: .6rem; flex-wrap: wrap; }
.label { font-size: .72rem; text-transform: uppercase; letter-spacing: .1em; color: var(--faint); }
.forecast { width: 100%; border-collapse: collapse; font-size: .88rem; margin-top: .6rem; }
.forecast td { padding: .3rem 0; border-top: 1px dotted var(--rule); }
.forecast td:last-child { text-align: right; }
.headline { margin-bottom: .85rem; }
.headline a { color: var(--ink); text-decoration: none; font-weight: bold; line-height: 1.35; }
.headline a:hover { color: var(--accent); }
.headline .src { font-size: .7rem; text-transform: uppercase; letter-spacing: .1em; color: var(--faint); display: block; margin-top: .15rem; }
.item { border-top: 1px dotted var(--rule); padding: .5rem 0; font-size: .92rem; line-height: 1.4; }
.item:first-of-type { border-top: none; }
.item .meta { color: var(--faint); font-size: .8rem; }
.note { color: var(--faint); font-style: italic; font-size: .9rem; }
.colophon {
  border-top: 4px double var(--ink); margin-top: .5rem; padding-top: .8rem;
  text-align: center; font-size: .75rem; color: var(--faint);
  text-transform: uppercase; letter-spacing: .15em;
}
@media print { body { background: none; padding: 0; } .sheet { box-shadow: none; } }
"""


def _weather_html(d: dict) -> str:
    rows = "".join(
        f"<tr><td>{escape(datetime.date.fromisoformat(day['date']).strftime('%a'))}"
        f" · {escape(day['condition'])}</td>"
        f"<td>{day['high']}/{day['low']}{escape(d['unit'])} · {day['precip_chance']}%</td></tr>"
        for day in d["days"]
    )
    return f"""
    <div class="stat-row">
      <div class="bignum">{d['current_temp']}{escape(d['unit'])}</div>
      <div>
        <div><strong>{escape(d['condition'])}</strong>, feels like {d['feels_like']}{escape(d['unit'])}</div>
        <div class="label">Wind {d['wind_mph']} mph · Sun {escape(d['sunrise'])}–{escape(d['sunset'])}</div>
      </div>
    </div>
    <table class="forecast">{rows}</table>"""


def _surf_html(d: dict) -> str:
    rows = "".join(
        f"<tr><td>{escape(datetime.date.fromisoformat(day['date']).strftime('%a'))}</td>"
        f"<td>{day['max_height_ft']} ft @ {day['max_period_s']}s</td></tr>"
        for day in d["days"]
    )
    return f"""
    <div class="stat-row">
      <div class="bignum">{d['wave_height_ft']}<small style="font-size:1.1rem"> ft</small></div>
      <div>
        <div><strong>{escape(d['rating'])}</strong></div>
        <div class="label">{escape(d['spot'])}</div>
        <div class="label">Swell {d['swell_height_ft']} ft @ {d['swell_period_s']}s from {escape(d['swell_direction'])}</div>
      </div>
    </div>
    <table class="forecast">{rows}</table>"""


def _news_html(d: dict) -> str:
    out = []
    for feed in d["feeds"]:
        if feed.get("error"):
            out.append(f'<p class="note">{escape(feed["name"])}: feed unavailable</p>')
            continue
        for item in feed["items"]:
            out.append(
                f'<div class="headline"><a href="{escape(item["link"])}">'
                f'{escape(item["title"])}</a>'
                f'<span class="src">{escape(feed["name"])}</span></div>'
            )
    return "".join(out)


def _gmail_html(d: dict) -> str:
    if not d["messages"]:
        return '<p class="note">Inbox zero. Savor it.</p>'
    items = "".join(
        f'<div class="item"><strong>{escape(m["from"])}</strong> — '
        f'{escape(m["subject"])}<div class="meta">{escape(m["snippet"])}</div></div>'
        for m in d["messages"]
    )
    return f'<p class="label">{d["total_unread"]} unread</p>{items}'


def _calendar_html(d: dict) -> str:
    if not d["events"]:
        return '<p class="note">A blank page — the whole day is yours.</p>'
    return "".join(
        f'<div class="item"><strong>{escape(e["time"])}</strong> — {escape(e["title"])}'
        + (f'<div class="meta">{escape(e["location"])}</div>' if e["location"] else "")
        + "</div>"
        for e in d["events"]
    )


RENDERERS = {
    "weather": ("The Weather", _weather_html),
    "surf": ("Surf Report", _surf_html),
    "news": ("The Wire", _news_html),
    "gmail": ("Correspondence", _gmail_html),
    "calendar": ("Today's Engagements", _calendar_html),
}

# Print order: personal columns first, news last (it's the longest).
SECTION_ORDER = ["calendar", "gmail", "weather", "surf", "news"]


def render(sections: dict, briefing: str | None, config: dict) -> str:
    paper = config["paper"]
    now = datetime.datetime.now()
    date_line = now.strftime("%A, %B %-d, %Y")

    body = []
    for name in SECTION_ORDER:
        if name not in sections:
            continue
        title, renderer = RENDERERS[name]
        section = sections[name]
        if section.get("error"):
            inner = f'<p class="note">This desk is dark today: {escape(section["error"])}</p>'
        else:
            inner = renderer(section["data"])
        body.append(f'<section><h2><span>◆</span> {escape(title)}</h2>{inner}</section>')

    briefing_html = (
        f'<div class="briefing">{escape(briefing)}</div>' if briefing else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(paper['title'])} — {escape(date_line)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="sheet">
  <header class="masthead">
    <h1>{escape(paper['title'])}</h1>
    <div class="dateline">
      <span>{escape(date_line)}</span>
      <span>{escape(paper.get('motto', ''))}</span>
      <span>Vol. 1 · Free of charge</span>
    </div>
  </header>
  {briefing_html}
  <main class="columns">{''.join(body)}</main>
  <footer class="colophon">Printed at {now.strftime('%-I:%M %p')} · Now put the phone down</footer>
</div>
</body>
</html>"""
