"""Today's agenda via the Google Calendar API.

Optional section — shares OAuth credentials with the Gmail section.
"""

import datetime
from zoneinfo import ZoneInfo

from .gmail_unread import _credentials


def fetch(config: dict) -> dict:
    from googleapiclient.discovery import build

    cfg = config["sections"]["calendar"]
    tz = ZoneInfo(config["paper"].get("timezone", "UTC"))
    now = datetime.datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + datetime.timedelta(days=1)

    service = build("calendar", "v3", credentials=_credentials())
    result = service.events().list(
        calendarId=cfg.get("calendar_id", "primary"),
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for event in result.get("items", []):
        start_raw = event["start"].get("dateTime") or event["start"].get("date")
        if "T" in start_raw:
            when = datetime.datetime.fromisoformat(start_raw).strftime("%-I:%M %p")
        else:
            when = "All day"
        events.append({
            "time": when,
            "title": event.get("summary", "(untitled)"),
            "location": event.get("location", ""),
        })

    return {"date": now.strftime("%A, %B %-d"), "events": events}
