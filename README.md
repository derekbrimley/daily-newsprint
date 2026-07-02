# 🗞️ The Daily Newsprint

A personal morning newspaper, generated fresh every day: unread email,
today's calendar, the surf report, weather, headlines, and a long read pulled
from your Readwise Reader queue — one page you can read with your coffee so
you don't have to touch your phone until later. Also renders a compact
front-page PNG for a color e-ink display.

```
python -m newsprint.build        # prints today's edition to output/index.html
```

The weather, surf, and news sections need **no API keys at all** (Open-Meteo
and public RSS feeds), so it works out of the box. Gmail, Calendar, and the
Claude-written front-page briefing are optional upgrades.

## How it works

```
config.yaml ──▶ newsprint/build.py
                   │  runs each enabled section (failures don't kill the paper)
                   ├─ sections/weather.py        Open-Meteo forecast (keyless)
                   ├─ sections/surf.py           Open-Meteo marine API (keyless)
                   ├─ sections/news.py           RSS headlines (keyless)
                   ├─ sections/gmail_unread.py   Gmail API (OAuth, optional)
                   ├─ sections/calendar_today.py Calendar API (OAuth, optional)
                   ├─ sections/reader.py         Readwise Reader long read (optional)
                   ├─ summarize.py               Claude editor's briefing (optional)
                   ├─ render.py ──▶ output/index.html   (broadsheet front page)
                   │                output/article.html (today's long read)
                   └─ eink.py   ──▶ output/eink.png     (e-ink display card)
```

Each section is a module with one `fetch(config) -> dict` function. To add a
section (stock prices, Strava, air quality...), drop a module in
`newsprint/sections/`, register it in `build.py`'s `FETCHERS`, and add a
renderer in `render.py`.

## Setup

```bash
pip install -r requirements.txt
# edit config.yaml: your location, surf spot, feeds, timezone
python -m newsprint.build
open output/index.html
```

### Readwise Reader long read (optional)

Each edition features one article from your Reader queue — front-page teaser
plus the full text on `article.html`. Get a token at
[readwise.io/access_token](https://readwise.io/access_token) and set it as
`READWISE_TOKEN`. In `config.yaml` you can choose which list to pull from
(`later` by default), the pick strategy (`oldest` clears your backlog,
`random` keeps it interesting), and whether printing an article archives it
(`archive_after_print: true` — the Printernet move: your queue actually
shrinks as you read the paper).

### Claude briefing (optional) — API key or your Claude subscription

Claude reads the day's data and writes the italic front-page editor's note.
Two ways to pay for it, set via `sections.briefing.provider`:

| provider | How it runs | Cost |
|---|---|---|
| `claude-cli` | Shells out to the Claude Code CLI (`claude -p`) on your machine | Covered by your Claude Pro/Max **subscription** — no API key |
| `api` | Anthropic API via the `anthropic` SDK (`ANTHROPIC_API_KEY`) | Pay-per-token, a fraction of a cent per edition |
| `auto` (default) | CLI if `claude` is on PATH, otherwise the API | — |

If you run the paper on your own machine or a Pi via cron, install
[Claude Code](https://claude.com/claude-code), log in once, and the briefing
rides on your subscription. On GitHub Actions, use an API key secret —
CI isn't covered by a personal subscription login.

### E-ink display (optional)

The build also renders `output/eink.png` — a compact, high-contrast front
page (weather, surf, agenda, mail count, top headlines, today's long read)
sized for a 7.3" color e-ink panel (800×480; change `eink.width/height` in
`config.yaml` for other panels). It needs Chromium for rendering:

```bash
pip install playwright && playwright install chromium
```

If your display already rotates images on a refresh cycle (like an Inky
dashboard pulling image URLs), just add the published PNG to its rotation —
e.g. `https://<user>.github.io/daily-newsprint/eink.png` when using the
GitHub Pages workflow, or the local file path when building on the Pi
itself. No changes needed on the display side.

### Gmail & Calendar (optional)

1. In [Google Cloud Console](https://console.cloud.google.com/), create a
   project, enable the **Gmail API** and **Calendar API**, and create an
   **OAuth client ID** of type *Desktop app*. Download it as `credentials.json`
   into the repo root (it's gitignored).
2. `pip install google-api-python-client google-auth-oauthlib`
   (also uncomment those lines in `requirements.txt`).
3. `python scripts/google_auth.py` — approve access in the browser; it writes
   `token.json` (also gitignored).
4. Flip `gmail.enabled` and `calendar.enabled` to `true` in `config.yaml`.

## Delivering it every morning

Pick whichever fits how you live:

**GitHub Actions + GitHub Pages (built in).** `.github/workflows/daily.yml`
builds the paper on a cron and publishes to GitHub Pages. Enable it:
Settings → Pages → Source: *GitHub Actions*. Add secrets as needed
(`ANTHROPIC_API_KEY`, and `GOOGLE_TOKEN_JSON` = contents of `token.json`,
plus a repo *variable* `GOOGLE_SECTIONS_ENABLED=true`). Bookmark the Pages
URL on your e-reader, kitchen tablet, or laptop. Note: a public Pages site is
public — keep the repo private or skip email/calendar sections there.

**Local cron (most private).** Everything stays on your machine:

```cron
0 6 * * * cd ~/daily-newsprint && python -m newsprint.build
```

Open `output/index.html` in the morning, or `python -m http.server -d output`
on a home server / Raspberry Pi with a hallway display.

**Email it to yourself.** Add a step that sends `output/index.html` via SMTP
or the Gmail API — it renders fine as an HTML email.

**Print it.** The stylesheet has print rules. `weasyprint output/index.html
newsprint.pdf` and a cheap thermal or laser printer gets you an actual
physical paper. Peak phone avoidance.

## Ideas for more sections

- Stocks/crypto watchlist (e.g. Stooq CSV endpoint, keyless)
- Air quality (Open-Meteo air quality API, keyless)
- Word of the day / on this day in history (Wikipedia API)
- Strava/fitness summary, sports scores, package tracking
