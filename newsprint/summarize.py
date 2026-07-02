"""Optional front-page "editor's briefing" written by Claude.

Two providers, chosen by sections.briefing.provider in config.yaml:

  claude-cli — shells out to the Claude Code CLI (`claude -p`). Runs on your
               own machine and is covered by a Claude Pro/Max subscription;
               no API key or per-token billing.
  api        — the Anthropic API via the `anthropic` SDK. Needs
               ANTHROPIC_API_KEY; costs a fraction of a cent per edition.
               This is what you want on GitHub Actions.
  auto       — (default) use the CLI if `claude` is on PATH, else the API.

Skipped gracefully when neither is available.
"""

import json
import shutil
import subprocess

SYSTEM = (
    "You are the editor of a one-reader morning newspaper. Write a single "
    "warm, punchy paragraph (3-5 sentences, no headers, no lists) that "
    "briefs the reader on their day: weather worth knowing, whether the "
    "surf is worth it, anything urgent in email or on the calendar, the one "
    "or two news stories that actually matter, and a nod to today's long "
    "read if there is one. Plain prose, light wit, no emoji."
)


def _digest(sections: dict) -> dict:
    """Trim raw section data so the prompt stays small and cheap."""
    digest = {}
    for name, section in sections.items():
        if section.get("error") or not section.get("data"):
            continue
        data = dict(section["data"])
        if name == "news":
            data = {"headlines": [
                item["title"] for feed in data["feeds"] for item in feed["items"][:3]
            ]}
        elif name == "reader":
            article = data.get("article")
            data = {k: article[k] for k in ("title", "author", "summary", "reading_minutes")} \
                if article else {}
        digest[name] = data
    return digest


def _via_cli(prompt: str) -> str | None:
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=300,
        )
        text = result.stdout.strip()
        return text if result.returncode == 0 and text else None
    except Exception:
        return None


def _via_api(prompt: str, model: str) -> str | None:
    try:
        import anthropic
        response = anthropic.Anthropic().messages.create(
            model=model,
            max_tokens=1024,
            thinking={"type": "adaptive"},
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return next(b.text for b in response.content if b.type == "text").strip()
    except Exception:
        return None


def write_briefing(sections: dict, config: dict) -> str | None:
    cfg = config["sections"]["briefing"]
    provider = cfg.get("provider", "auto")
    prompt = "Today's raw data:\n" + json.dumps(_digest(sections), indent=2)

    if provider in ("auto", "claude-cli") and shutil.which("claude"):
        # The CLI takes one combined prompt; instructions go inline.
        briefing = _via_cli(f"{SYSTEM}\n\n{prompt}")
        if briefing or provider == "claude-cli":
            return briefing

    if provider in ("auto", "api"):
        return _via_api(prompt, cfg.get("model", "claude-opus-4-8"))

    return None
