# Project context for Claude Code

The Daily Newsprint: a personal morning newspaper generator. `python -m
newsprint.build` fetches each enabled section from `config.yaml`, renders a
broadsheet-styled `output/index.html`, the day's Readwise long read as
`output/article.html`, and an 800×480 `output/eink.png` for a color e-ink
display. Read README.md for the full architecture.

Key facts:

- Each section is a module in `newsprint/sections/` exposing
  `fetch(config) -> dict`, registered in `build.py` `FETCHERS` with a
  matching renderer in `render.py`. Section failures degrade gracefully —
  never let one section kill the build.
- Weather/surf (Open-Meteo) and news (RSS) are keyless. Gmail/Calendar need
  Google OAuth (`scripts/google_auth.py` → `token.json`). The long read
  needs `READWISE_TOKEN`. All credential files are gitignored — keep it
  that way.
- The front-page briefing (`newsprint/summarize.py`) supports
  `provider: claude-cli` (shells out to `claude -p`, billed to the user's
  Claude subscription — preferred locally) or `provider: api`
  (ANTHROPIC_API_KEY). Default `auto` prefers the CLI.
- The e-ink PNG is a Playwright/Chromium screenshot of `eink.py`'s compact
  HTML. `NEWSPRINT_CHROMIUM=<path>` uses a system Chromium instead of the
  Playwright download (needed on Raspberry Pi).
- **This deployment is private-only.** The owner does not want anything
  published publicly. Do not enable GitHub Pages or any public hosting;
  `.github/workflows/daily.yml` (Pages deploy) exists from an earlier plan
  and should not be activated — prefer deleting it or leaving it dormant.
  Delivery is local: cron + local files, optionally served on the LAN only.
- The owner's separate `inky-dashboard` repo drives a 7.3" color e-ink
  display that rotates images every 15 minutes; integration is done by
  adding `output/eink.png` (local path or LAN URL) to that rotation.
