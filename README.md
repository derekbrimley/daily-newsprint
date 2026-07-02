# 🗞️ The Daily Newsprint

A personal morning newspaper, generated fresh every day: unread email,
today's calendar, the surf report, weather, and headlines — one page you can
read with your coffee so you don't have to touch your phone until later.

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
                   ├─ summarize.py               Claude editor's briefing (optional)
                   └─ render.py ──▶ output/index.html  (broadsheet-styled page)
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

### Claude briefing (optional)

Set `ANTHROPIC_API_KEY` in your environment. Claude reads the day's data and
writes a short front-page editor's note. Costs a fraction of a cent per day.

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
- "Long read of the day" pulled from your read-later queue
