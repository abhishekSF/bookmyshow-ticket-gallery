"""Connected App OAuth for Ticket__c create/update. Stores refresh token locally."""

from __future__ import annotations

import http.server
import json
import sys
import urllib.parse
import webbrowser
from pathlib import Path

import httpx

from config import REPO_ROOT, settings

REDIRECT = "http://localhost:8765/callback"
SCOPES = "api refresh_token"


def setup_salesforce_oauth() -> None:
    client_id = settings.sf_client_id
    client_secret = settings.sf_client_secret
    login_url = (settings.sf_url or "https://login.salesforce.com").rstrip("/")
    if not client_id or not client_secret:
        print("Create a Connected App with callback", REDIRECT)
        print("OAuth scopes: Manage user data via APIs (api), Perform requests at any time (refresh_token)")
        print("Set SF_CLIENT_ID and SF_CLIENT_SECRET in .env")
        sys.exit(1)

    params = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": REDIRECT,
            "scope": SCOPES,
        }
    )
    auth_url = f"{login_url}/services/oauth2/authorize?{params}"
    code_holder: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return
            query = urllib.parse.parse_qs(parsed.query)
            code_holder["code"] = (query.get("code") or [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Salesforce auth complete. You can close this tab.")

        def log_message(self, fmt, *args):  # noqa: A003
            return

    print("Opening browser for Salesforce consent…")
    webbrowser.open(auth_url)
    server = http.server.HTTPServer(("127.0.0.1", 8765), Handler)
    while "code" not in code_holder:
        server.handle_request()
    server.server_close()
    if not code_holder.get("code"):
        raise SystemExit("No auth code returned")

    response = httpx.post(
        f"{login_url}/services/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "code": code_holder["code"],
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT,
        },
        timeout=30.0,
    )
    if response.status_code >= 400:
        raise SystemExit(f"Token exchange failed: {response.text[:500]}")
    data = response.json()
    token_path = Path(settings.sf_token_file)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(
        json.dumps(
            {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "instance_url": data.get("instance_url"),
                "client_id": client_id,
                "login_url": login_url,
            },
            indent=2,
        )
    )
    print(f"Saved Salesforce tokens to {token_path.relative_to(REPO_ROOT)}")
    print("Ticket__c create/update only. Then: python main_scraper.py dry-run")


if __name__ == "__main__":
    setup_salesforce_oauth()
