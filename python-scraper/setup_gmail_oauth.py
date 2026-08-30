"""Gmail OAuth setup. Requests gmail.readonly only. Never modify or send."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from config import GMAIL_SCOPES, REPO_ROOT, settings

FORBIDDEN = ("gmail.modify", "gmail.send", "gmail.compose", "gmail.insert")


def setup_gmail_oauth() -> None:
    for scope in GMAIL_SCOPES:
        lowered = scope.lower()
        if any(bad in lowered for bad in FORBIDDEN):
            raise SystemExit(f"refusing scope {scope}")
        if "gmail.readonly" not in lowered:
            raise SystemExit("scope must be gmail.readonly")

    client_id = settings.gmail_client_id
    client_secret = settings.gmail_client_secret
    if not client_id or not client_secret:
        print("Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env")
        print("Google Cloud → APIs → Credentials → OAuth client → Desktop app")
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, list(GMAIL_SCOPES))
    creds = flow.run_local_server(port=0, prompt="consent")
    token_path = Path(settings.gmail_token_file)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    creds_path = Path(settings.gmail_credentials_file)
    creds_path.write_text(json.dumps(client_config, indent=2))
    print(f"Saved readonly token to {token_path.relative_to(REPO_ROOT)}")
    print("Next: python main_scraper.py fetch")


if __name__ == "__main__":
    setup_gmail_oauth()
