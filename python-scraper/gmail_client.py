"""
Gmail fetch: readonly OAuth, BookMyShow booking/confirmation/ticket mail,
raw messages saved on disk by message id. Never requests modify or send.
"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import GMAIL_SCOPES, RAW_EMAIL_DIR, settings

FORBIDDEN_SCOPES = (
    "gmail.modify",
    "gmail.send",
    "gmail.compose",
    "gmail.insert",
    "mail.google.com",
)

BOOKMYSHOW_QUERY = (
    "(from:noreply@bookmyshow.com OR from:bookmyshow.com "
    "OR from:tickets@bookmyshow.com OR from:books@bookmyshow.com) "
    "(subject:booking OR subject:confirmation OR subject:ticket)"
)


class GmailScopeError(RuntimeError):
    pass


def assert_readonly_scopes(scopes: Optional[List[str]]) -> None:
    joined = " ".join(scopes or GMAIL_SCOPES).lower()
    for bad in FORBIDDEN_SCOPES:
        if bad.lower() in joined and "gmail.readonly" not in bad:
            raise GmailScopeError(f"refusing Gmail scope {bad}; readonly only")
    if "gmail.readonly" not in joined:
        raise GmailScopeError("Gmail scope must be gmail.readonly")


def load_gmail_credentials() -> Credentials:
    token_path = Path(settings.gmail_token_file)
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), list(GMAIL_SCOPES))
        assert_readonly_scopes(getattr(creds, "scopes", None) or list(GMAIL_SCOPES))
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
    if not creds or not creds.valid:
        raise RuntimeError(
            "Gmail token missing or invalid. Run python setup_gmail_oauth.py"
        )
    return creds


def _decode_b64(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", "replace")


def _walk_parts(payload: Dict[str, Any], collected: Dict[str, str]) -> None:
    mime = (payload.get("mimeType") or "").lower()
    body = payload.get("body") or {}
    data = body.get("data")
    if data:
        text = _decode_b64(data)
        if "html" in mime:
            collected["html"] = collected.get("html") or text
        else:
            collected["text"] = collected.get("text") or text
    for part in payload.get("parts") or []:
        _walk_parts(part, collected)


def _headers_map(payload: Dict[str, Any]) -> Dict[str, str]:
    out = {}
    for header in payload.get("headers") or []:
        name = (header.get("name") or "").lower()
        if name in {"from", "subject", "date", "to"}:
            out[name] = header.get("value") or ""
    return out


def fetch_and_store(
    max_results: int = 50,
    query: str = BOOKMYSHOW_QUERY,
    raw_dir: Path = RAW_EMAIL_DIR,
) -> List[Path]:
    """Fetch matching messages and write one JSON file per message id."""
    creds = load_gmail_credentials()
    assert_readonly_scopes(list(creds.scopes or GMAIL_SCOPES))
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    raw_dir.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []
    page_token = None
    remaining = max_results
    try:
        while remaining > 0:
            batch = min(remaining, 50)
            response = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=batch, pageToken=page_token)
                .execute()
            )
            messages = response.get("messages") or []
            if not messages:
                break
            for meta in messages:
                message_id = meta["id"]
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message_id, format="full")
                    .execute()
                )
                payload = msg.get("payload") or {}
                bodies: Dict[str, str] = {}
                _walk_parts(payload, bodies)
                record = {
                    "id": message_id,
                    "thread_id": msg.get("threadId"),
                    "internal_date": msg.get("internalDate"),
                    "snippet": msg.get("snippet"),
                    "headers": _headers_map(payload),
                    "text": bodies.get("text") or "",
                    "html": bodies.get("html") or "",
                }
                path = raw_dir / f"{message_id}.json"
                path.write_text(json.dumps(record, indent=2, ensure_ascii=False))
                written.append(path)
                remaining -= 1
                if remaining <= 0:
                    break
            page_token = response.get("nextPageToken")
            if not page_token:
                break
    except HttpError as exc:
        raise RuntimeError(f"Gmail fetch failed: {exc}") from exc
    return written


def load_raw_emails(raw_dir: Path = RAW_EMAIL_DIR) -> List[Dict[str, Any]]:
    emails = []
    if not raw_dir.exists():
        return emails
    for path in sorted(raw_dir.glob("*.json")):
        emails.append(json.loads(path.read_text()))
    return emails


def email_text(email: Dict[str, Any]) -> str:
    html = email.get("html") or ""
    if html:
        try:
            from bs4 import BeautifulSoup

            html_text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        except Exception:
            html_text = re.sub(r"<[^>]+>", " ", html)
    else:
        html_text = ""
    headers = email.get("headers") or {}
    parts = [
        headers.get("subject", ""),
        headers.get("from", ""),
        email.get("text") or "",
        html_text,
        email.get("snippet") or "",
    ]
    return "\n".join(p for p in parts if p)
