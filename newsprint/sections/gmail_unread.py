"""Unread email summary via the Gmail API.

Optional section — requires Google OAuth credentials. See README for setup.
Expects a token file at the path in GOOGLE_TOKEN_FILE (default: token.json)
created by scripts/google_auth.py.
"""

import os


def _credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    token_file = os.environ.get("GOOGLE_TOKEN_FILE", "token.json")
    if not os.path.exists(token_file):
        raise RuntimeError(
            f"Google token file not found at {token_file}. "
            "Run scripts/google_auth.py first (see README)."
        )
    creds = Credentials.from_authorized_user_file(token_file)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def fetch(config: dict) -> dict:
    from googleapiclient.discovery import build

    cfg = config["sections"]["gmail"]
    service = build("gmail", "v1", credentials=_credentials())

    result = service.users().messages().list(
        userId="me",
        q=cfg.get("query", "is:unread category:primary"),
        maxResults=cfg.get("max_messages", 10),
    ).execute()

    messages = []
    for ref in result.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=ref["id"], format="metadata",
            metadataHeaders=["From", "Subject"],
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        sender = headers.get("From", "Unknown")
        # "Jane Doe <jane@example.com>" -> "Jane Doe"
        if "<" in sender:
            sender = sender.split("<")[0].strip().strip('"')
        messages.append({
            "from": sender,
            "subject": headers.get("Subject", "(no subject)"),
            "snippet": msg.get("snippet", "")[:200],
        })

    return {
        "total_unread": result.get("resultSizeEstimate", len(messages)),
        "messages": messages,
    }
