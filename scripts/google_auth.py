"""One-time local OAuth flow for the Gmail and Calendar sections.

1. In Google Cloud Console, create an OAuth client (Desktop app) with the
   Gmail API and Calendar API enabled, and download credentials.json here.
2. Run: python scripts/google_auth.py
3. A browser opens; approve access. token.json is written for the builder.

For GitHub Actions, paste the contents of token.json into a repo secret
named GOOGLE_TOKEN_JSON.
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

with open("token.json", "w") as f:
    f.write(creds.to_json())

print("✓ token.json written — the gmail and calendar sections can now run.")
