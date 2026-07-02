"""Optional front-page "editor's briefing" written by Claude.

Skipped gracefully when no Anthropic credentials are available.
"""

import json


def write_briefing(sections: dict, config: dict) -> str | None:
    try:
        import anthropic
    except ImportError:
        return None

    model = config["sections"]["briefing"].get("model", "claude-opus-4-8")

    # Trim the raw section data so the prompt stays small and cheap.
    digest = {}
    for name, section in sections.items():
        if section.get("error"):
            continue
        data = dict(section["data"])
        if name == "news":
            data = {
                "headlines": [
                    item["title"]
                    for feed in data["feeds"]
                    for item in feed["items"][:3]
                ]
            }
        digest[name] = data

    client = anthropic.Anthropic()
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            thinking={"type": "adaptive"},
            system=(
                "You are the editor of a one-reader morning newspaper. Write a "
                "single warm, punchy paragraph (3-5 sentences, no headers, no "
                "lists) that briefs the reader on their day: weather worth "
                "knowing, whether the surf is worth it, anything urgent in "
                "email or on the calendar, and the one or two news stories "
                "that actually matter. Plain prose, light wit, no emoji."
            ),
            messages=[{
                "role": "user",
                "content": "Today's raw data:\n" + json.dumps(digest, indent=2),
            }],
        )
        return next(b.text for b in response.content if b.type == "text").strip()
    except Exception:
        return None
