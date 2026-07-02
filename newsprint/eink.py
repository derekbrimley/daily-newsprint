"""Compact front-page image for a color e-ink display.

Renders a high-contrast, display-sized HTML page and screenshots it to
output/eink.png via Playwright. The e-ink dashboard then just needs to pull
that PNG like any other image in its rotation.

E-ink friendly choices: pure white paper, pure black ink, one saturated
accent (red), no grays or gradients that would dither badly.
"""

import datetime
import os
from html import escape

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: {W}px; height: {H}px; overflow: hidden;
  background: #ffffff; color: #000000;
  font-family: Georgia, 'Times New Roman', serif;
  display: flex; flex-direction: column; padding: 14px 18px;
}
header { border-bottom: 4px double #000; padding-bottom: 6px; display: flex; justify-content: space-between; align-items: baseline; }
header h1 { font-size: 26px; font-variant: small-caps; font-weight: 900; }
header .date { font-size: 14px; text-transform: uppercase; letter-spacing: .1em; }
.cols { flex: 1; display: flex; gap: 18px; padding-top: 10px; min-height: 0; }
.col { flex: 1; min-width: 0; }
h2 { font-size: 12px; text-transform: uppercase; letter-spacing: .16em;
     border-bottom: 2px solid #000; padding-bottom: 2px; margin: 10px 0 6px; }
h2:first-child { margin-top: 0; }
h2 span { color: #c0201a; }
.bignum { font-size: 52px; font-weight: 900; line-height: 1; }
.wx { display: flex; gap: 12px; align-items: baseline; }
.wx .detail { font-size: 14px; line-height: 1.35; }
.line { font-size: 14px; line-height: 1.4; padding: 3px 0; border-bottom: 1px dotted #999; }
.line strong { font-weight: 700; }
.line:last-child { border-bottom: none; }
.rating { color: #c0201a; font-weight: 700; }
footer { border-top: 2px solid #000; padding-top: 5px; font-size: 12px;
         display: flex; justify-content: space-between; }
footer .accent { color: #c0201a; }
"""


def _lines(items: list[str], limit: int) -> str:
    return "".join(f'<div class="line">{item}</div>' for item in items[:limit])


def build_html(sections: dict, config: dict) -> str:
    eink = config.get("eink", {})
    w, h = eink.get("width", 800), eink.get("height", 480)
    now = datetime.datetime.now()

    left, right = [], []

    wx = sections.get("weather", {}).get("data")
    if wx:
        today = wx["days"][0]
        left.append(f"""<h2><span>◆</span> Weather</h2>
        <div class="wx"><div class="bignum">{wx['current_temp']}°</div>
        <div class="detail"><strong>{escape(wx['condition'])}</strong><br>
        H {today['high']}° / L {today['low']}° · {today['precip_chance']}% rain<br>
        Wind {wx['wind_mph']} mph</div></div>""")

    surf = sections.get("surf", {}).get("data")
    if surf:
        left.append(f"""<h2><span>◆</span> Surf — {escape(surf['spot'].split(',')[0])}</h2>
        <div class="line"><strong>{surf['wave_height_ft']} ft @ {surf['wave_period_s']}s</strong>
        from {escape(surf['swell_direction'])} · <span class="rating">{escape(surf['rating'])}</span></div>""")

    cal = sections.get("calendar", {}).get("data")
    if cal is not None:
        events = [f"<strong>{escape(e['time'])}</strong> {escape(e['title'])}"
                  for e in cal["events"]] or ["Nothing scheduled"]
        left.append(f'<h2><span>◆</span> Today</h2>{_lines(events, 5)}')

    gmail = sections.get("gmail", {}).get("data")
    if gmail:
        msgs = [f"<strong>{escape(m['from'])}</strong> — {escape(m['subject'][:52])}"
                for m in gmail["messages"]] or ["Inbox zero"]
        right.append(f'<h2><span>◆</span> Mail ({gmail["total_unread"]} unread)</h2>{_lines(msgs, 3)}')

    news = sections.get("news", {}).get("data")
    if news:
        heads = [escape(item["title"][:78])
                 for feed in news["feeds"] for item in feed["items"][:2]]
        right.append(f'<h2><span>◆</span> The Wire</h2>{_lines(heads, 6)}')

    article = (sections.get("reader", {}).get("data") or {}).get("article")
    long_read = (
        f'<span>Long read: <span class="accent">{escape(article["title"][:60])}</span>'
        f' · {article["reading_minutes"]} min</span>'
        if article else "<span></span>"
    )

    css = CSS.replace("{W}", str(w)).replace("{H}", str(h))
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}</style></head>
<body>
<header><h1>{escape(config['paper']['title'])}</h1>
<div class="date">{now.strftime('%a, %b %-d')}</div></header>
<div class="cols">
  <div class="col">{''.join(left)}</div>
  <div class="col">{''.join(right)}</div>
</div>
<footer>{long_read}<span>Printed {now.strftime('%-I:%M %p')}</span></footer>
</body></html>"""


def render_png(html: str, out_path: str, config: dict) -> bool:
    """Screenshot the e-ink page to a PNG. Returns False if Playwright is missing."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False

    eink = config.get("eink", {})
    w, h = eink.get("width", 800), eink.get("height", 480)

    # NEWSPRINT_CHROMIUM lets you use a system Chromium instead of the
    # Playwright download (handy on a Raspberry Pi: apt install chromium).
    exe = os.environ.get("NEWSPRINT_CHROMIUM")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        page.set_content(html)
        page.screenshot(path=out_path)
        browser.close()
    return True
