"""
Salesforce write adapter. Reads tickets.json only. Never reads Gmail.

Headless 360 PATCH by Booking_Id__c first, REST sObject upsert fallback.
Dry-run before every real push. No --confirm, no write.
--confirm cannot push complete: false.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol, Sequence
from urllib.parse import quote

import httpx

from config import settings

SHARED = Path(__file__).resolve().parent.parent / "shared-config"
sys.path.insert(0, str(SHARED))

from ticket_helpers import (  # noqa: E402
    IncompleteTicketError,
    sample_payload_fields,
    ticket_to_salesforce,
)


class TicketWriteAdapter(Protocol):
    def existing_booking_ids(self, booking_ids: Sequence[str]) -> set[str]:
        ...

    def upsert(self, booking_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...


class AdapterRefused(RuntimeError):
    pass


@dataclass
class DryRunSummary:
    total: int = 0
    complete: int = 0
    incomplete: int = 0
    would_create: int = 0
    would_update: int = 0
    would_skip: int = 0
    sample_payload: Optional[Dict[str, Any]] = None
    skip_reasons: List[str] = field(default_factory=list)

    def lines(self) -> str:
        sample = "{ " + ", ".join(sample_payload_fields()) + " }"
        if self.sample_payload:
            sample = json.dumps(self.sample_payload, ensure_ascii=False)
        return (
            "Dry-run summary\n"
            "---------------\n"
            f"Total tickets:      {self.total}\n"
            f"Complete:           {self.complete}\n"
            f"Incomplete:         {self.incomplete:>2}\n"
            f"Would create:       {self.would_create}\n"
            f"Would update:        {self.would_update}\n"
            f"Would skip:          {self.would_skip}\n"
            f"\nSample payload: {sample}"
        )


def load_tickets(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict) and "tickets" in data:
        return list(data["tickets"])
    if isinstance(data, list):
        return data
    raise ValueError(f"tickets.json must be a list or {{tickets: [...]}}: {path}")


def summarize(
    tickets: Sequence[Dict[str, Any]],
    existing_ids: Optional[Iterable[str]] = None,
    refusals: Optional[Iterable[str]] = None,
) -> DryRunSummary:
    existing = set(existing_ids or [])
    refused = set(refusals or [])
    summary = DryRunSummary(total=len(tickets))
    sample = None
    for ticket in tickets:
        if ticket.get("complete"):
            summary.complete += 1
            booking_id = ticket.get("booking_id")
            try:
                payload = ticket_to_salesforce(ticket)
            except IncompleteTicketError:
                summary.would_skip += 1
                summary.incomplete += 1
                summary.skip_reasons.append(f"{booking_id}: complete flag lie")
                continue
            if booking_id in refused:
                summary.would_skip += 1
                summary.skip_reasons.append(f"{booking_id}: adapter refusal")
                continue
            if booking_id in existing:
                summary.would_update += 1
            else:
                summary.would_create += 1
            if sample is None:
                sample = {k: payload.get(k) for k in sample_payload_fields()}
        else:
            summary.incomplete += 1
            summary.would_skip += 1
    summary.sample_payload = sample
    return summary


def print_dry_run(summary: DryRunSummary) -> None:
    print(summary.lines())


def write_set(tickets: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Complete records only. complete: false never enters this list."""
    selected = []
    for ticket in tickets:
        if not ticket.get("complete"):
            continue
        ticket_to_salesforce(ticket)  # raises if the flag is a lie
        selected.append(ticket)
    return selected


class RestAdapter:
    """PATCH /sobjects/Ticket__c/Booking_Id__c/{id}"""

    def __init__(self, access_token: str, instance_url: str, api_version: str):
        self.access_token = access_token
        self.instance_url = instance_url.rstrip("/")
        self.api_version = api_version if api_version.startswith("v") else f"v{api_version}"

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def existing_booking_ids(self, booking_ids: Sequence[str]) -> set[str]:
        ids = [i for i in booking_ids if i]
        if not ids:
            return set()
        quoted = ",".join("'" + i.replace("'", "\\'") + "'" for i in ids)
        soql = f"SELECT Booking_Id__c FROM Ticket__c WHERE Booking_Id__c IN ({quoted})"
        url = f"{self.instance_url}/services/data/{self.api_version}/query"
        try:
            response = httpx.get(
                url, headers=self._headers, params={"q": soql}, timeout=30.0
            )
            response.raise_for_status()
            return {
                row["Booking_Id__c"]
                for row in response.json().get("records", [])
                if row.get("Booking_Id__c")
            }
        except httpx.HTTPError:
            return set()

    def upsert(self, booking_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        encoded = quote(str(booking_id), safe="")
        url = (
            f"{self.instance_url}/services/data/{self.api_version}"
            f"/sobjects/Ticket__c/Booking_Id__c/{encoded}"
        )
        body = {k: v for k, v in payload.items() if k != "Booking_Id__c"}
        response = httpx.patch(url, headers=self._headers, json=body, timeout=30.0)
        if response.status_code not in {200, 201, 204}:
            raise AdapterRefused(
                f"REST upsert failed {response.status_code}: {response.text[:500]}"
            )
        return {
            "adapter": "rest",
            "status": response.status_code,
            "created": response.status_code == 201,
            "booking_id": booking_id,
        }


class Headless360Adapter:
    """
    Headless 360 Dispatch PATCH by Booking_Id__c.

    Uses the same Connected App OAuth token as REST. If Dispatch is
    unavailable (beta org, MCP-specific auth), the caller falls back.
    """

    def __init__(
        self,
        access_token: str,
        instance_url: str,
        api_version: str,
        mcp_url: Optional[str] = None,
    ):
        self.access_token = access_token
        self.instance_url = instance_url.rstrip("/")
        self.api_version = api_version if api_version.startswith("v") else f"v{api_version}"
        self.mcp_url = mcp_url or settings.sf_headless_360_url
        self._rest = RestAdapter(access_token, instance_url, api_version)

    def existing_booking_ids(self, booking_ids: Sequence[str]) -> set[str]:
        return self._rest.existing_booking_ids(booking_ids)

    def upsert(self, booking_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        encoded = quote(str(booking_id), safe="")
        target = (
            f"{self.instance_url}/services/data/{self.api_version}"
            f"/sobjects/Ticket__c/Booking_Id__c/{encoded}"
        )
        body = {k: v for k, v in payload.items() if k != "Booking_Id__c"}
        rpc = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "Dispatch",
                "arguments": {
                    "url": target,
                    "method": "PATCH",
                    "headers": {
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    "body": body,
                },
            },
        }
        try:
            response = httpx.post(
                self.mcp_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=rpc,
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise AdapterRefused(f"Headless 360 unreachable: {exc}") from exc
        if response.status_code >= 400:
            raise AdapterRefused(
                f"Headless 360 HTTP {response.status_code}: {response.text[:400]}"
            )
        data = response.json() if response.content else {}
        if isinstance(data, dict) and data.get("error"):
            raise AdapterRefused(str(data["error"])[:400])
        return {
            "adapter": "headless360",
            "status": response.status_code,
            "booking_id": booking_id,
            "body": data,
        }


class FallbackAdapter:
    def __init__(self, headless: Headless360Adapter, rest: RestAdapter):
        self.headless = headless
        self.rest = rest

    def existing_booking_ids(self, booking_ids: Sequence[str]) -> set[str]:
        return self.rest.existing_booking_ids(booking_ids)

    def upsert(self, booking_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.headless.upsert(booking_id, payload)
        except AdapterRefused as exc:
            print(f"Headless 360 failed ({exc}); REST fallback for {booking_id}")
            return self.rest.upsert(booking_id, payload)


def oauth_token() -> Dict[str, str]:
    token_path = Path(settings.sf_token_file)
    stored: Dict[str, Any] = {}
    if token_path.exists():
        stored = json.loads(token_path.read_text())
    refresh = settings.sf_refresh_token or stored.get("refresh_token")
    client_id = settings.sf_client_id or stored.get("client_id")
    client_secret = settings.sf_client_secret or stored.get("client_secret")
    login_url = (
        stored.get("login_url")
        or settings.sf_url
        or "https://login.salesforce.com"
    ).rstrip("/")
    if not (refresh and client_id):
        raise RuntimeError(
            "Salesforce OAuth missing. Set SF_CLIENT_ID / SF_REFRESH_TOKEN "
            "or run python setup_salesforce_oauth.py"
        )
    response = httpx.post(
        f"{login_url}/services/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret or "",
            "refresh_token": refresh,
        },
        timeout=30.0,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Salesforce token refresh failed: {response.text[:400]}")
    data = response.json()
    return {
        "access_token": data["access_token"],
        "instance_url": data.get("instance_url") or stored.get("instance_url") or "",
    }


def build_adapter(auth: Optional[Dict[str, str]] = None) -> FallbackAdapter:
    auth = auth or oauth_token()
    rest = RestAdapter(auth["access_token"], auth["instance_url"], settings.sf_api_version)
    headless = Headless360Adapter(
        auth["access_token"],
        auth["instance_url"],
        settings.sf_api_version,
        settings.sf_headless_360_url,
    )
    return FallbackAdapter(headless, rest)


def dry_run(
    tickets_path: Path,
    adapter: Optional[TicketWriteAdapter] = None,
) -> DryRunSummary:
    tickets = load_tickets(tickets_path)
    existing: set[str] = set()
    if adapter is not None:
        ids = [t.get("booking_id") for t in tickets if t.get("complete") and t.get("booking_id")]
        existing = adapter.existing_booking_ids(ids)
    summary = summarize(tickets, existing_ids=existing)
    print_dry_run(summary)
    return summary


def upsert_tickets(
    tickets_path: Path,
    confirm: bool = False,
    adapter: Optional[TicketWriteAdapter] = None,
) -> DryRunSummary:
    """
    Always prints a dry-run. Writes only when confirm=True, and only
    complete records. Incomplete stays in tickets.json / review.json.
    """
    tickets = load_tickets(tickets_path)
    live_adapter = adapter
    existing: set[str] = set()
    if live_adapter is None and confirm:
        live_adapter = build_adapter()
    if live_adapter is not None:
        ids = [t.get("booking_id") for t in tickets if t.get("complete") and t.get("booking_id")]
        existing = live_adapter.existing_booking_ids(ids)
    summary = summarize(tickets, existing_ids=existing)
    print_dry_run(summary)

    if not confirm:
        print("No --confirm, no write.")
        return summary

    if live_adapter is None:
        raise RuntimeError("Salesforce adapter required for --confirm")

    selected = write_set(tickets)
    for ticket in selected:
        payload = ticket_to_salesforce(ticket)
        live_adapter.upsert(ticket["booking_id"], payload)
    skipped = summary.would_skip
    print(f"Wrote {len(selected)} complete Ticket__c row(s); skipped {skipped}.")
    return summary
