"""Three locks: IST offset, no year from Gmail, --confirm refuses complete:false."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ticket_helpers import (
    IST_OFFSET,
    IncompleteTicketError,
    finalize_ticket,
    parse_show_date_iso,
    ticket_to_salesforce,
)

from salesforce_write import DryRunSummary, summarize, upsert_tickets, write_set


def _ticket(**overrides):
    ticket = {
        "booking_id": "BMS123456789",
        "movie_title": "Dune: Part Two",
        "cinema_raw": "PVR Forum Mall, Koramangala, Bengaluru",
        "cinema_name": "PVR Forum Mall",
        "city": "Bengaluru",
        "show_date_raw": "Sat, 15 Mar 2026, 7:30 PM",
        "show_date_iso": "2026-03-15T19:30:00+05:30",
        "seats": ["G12", "G13"],
        "seat_display": "G12, G13",
        "quantity": 2,
        "amount": 980,
        "currency": "INR",
        "poster_url": None,
        "poster_source": "fallback",
        "blurb": None,
        "source_message_id": "msg-1",
        "complete": True,
        "missing_fields": [],
    }
    ticket.update(overrides)
    return ticket


def _complete_ticket(**overrides):
    return finalize_ticket(_ticket(**overrides))


class FakeAdapter:
    def __init__(self, existing=None):
        self.existing = set(existing or [])
        self.written = []

    def existing_booking_ids(self, booking_ids):
        return self.existing.intersection(booking_ids)

    def upsert(self, booking_id, payload):
        self.written.append({"booking_id": booking_id, "payload": payload})
        return {"adapter": "fake", "booking_id": booking_id}


def test_lock1_iso_includes_ist_offset():
    iso = parse_show_date_iso(
        "Sat, 15 Mar 2026, 7:30 PM",
        cinema_raw="PVR Forum Mall, Koramangala, Bengaluru",
        city="Bengaluru",
    )
    assert iso is not None
    assert IST_OFFSET in iso
    assert iso.endswith("+05:30")
    assert iso == "2026-03-15T19:30:00+05:30"
    assert "Z" not in iso


def test_lock1_finalize_rejects_iso_without_offset():
    with pytest.raises(ValueError, match=r"\+05:30"):
        finalize_ticket(_ticket(show_date_iso="2026-03-15T19:30:00"))


def test_lock2_missing_year_stays_raw_only():
    iso = parse_show_date_iso(
        "Sat, 15 Mar, 7:30 PM",
        cinema_raw="PVR Forum Mall, Koramangala, Bengaluru",
        city="Bengaluru",
        received_at="2024-12-01T10:00:00Z",
    )
    assert iso is None


def test_lock2_received_time_does_not_supply_year():
    iso = parse_show_date_iso(
        "15 Mar, 7:30 PM",
        cinema_raw="INOX Bandra, Mumbai",
        received_at="2026-08-30T08:00:00+05:30",
    )
    assert iso is None
    ticket = finalize_ticket(
        _ticket(show_date_raw="15 Mar, 7:30 PM", show_date_iso=None)
    )
    assert ticket["show_date_iso"] is None
    payload = ticket_to_salesforce(ticket)
    assert payload["Show_Date_Text__c"] == "15 Mar, 7:30 PM"
    assert "Show_Date__c" not in payload


def test_lock2_non_indian_venue_no_iso():
    iso = parse_show_date_iso(
        "Sat, 15 Mar 2026, 7:30 PM",
        cinema_raw="Odeon Leicester Square, London",
        city="London",
    )
    assert iso is None


def test_lock3_confirm_refuses_complete_false(tmp_path: Path):
    incomplete = finalize_ticket(
        {
            "booking_id": "BMS_MISSING_abc",
            "movie_title": "Dune: Part Two",
            "cinema_raw": "PVR Forum Mall, Bengaluru",
            "cinema_name": "PVR Forum Mall",
            "city": "Bengaluru",
            "show_date_raw": "Sat, 15 Mar 2026, 7:30 PM",
            "show_date_iso": "2026-03-15T19:30:00+05:30",
            "seats": [],
            "source_message_id": "abc",
        }
    )
    assert incomplete["complete"] is False
    with pytest.raises(IncompleteTicketError):
        ticket_to_salesforce(incomplete)
    assert write_set([incomplete]) == []

    tickets_path = tmp_path / "tickets.json"
    tickets_path.write_text(json.dumps([incomplete, _complete_ticket()]))
    adapter = FakeAdapter()
    summary = upsert_tickets(tickets_path, confirm=True, adapter=adapter)
    assert isinstance(summary, DryRunSummary)
    assert [row["booking_id"] for row in adapter.written] == ["BMS123456789"]
    assert all(row["payload"]["Category__c"] == "Movie" for row in adapter.written)


def test_confirm_false_never_writes(tmp_path: Path):
    tickets_path = tmp_path / "tickets.json"
    tickets_path.write_text(json.dumps([_complete_ticket()]))
    adapter = FakeAdapter()
    upsert_tickets(tickets_path, confirm=False, adapter=adapter)
    assert adapter.written == []


def test_dry_run_counts_match_tickets_json():
    tickets = [
        _complete_ticket(),
        _complete_ticket(booking_id="BMS999"),
        finalize_ticket(
            {
                "booking_id": None,
                "movie_title": "Jawan",
                "show_date_raw": "Fri, 01 May 2026, 6:00 PM",
                "cinema_raw": "PVR Powai, Mumbai",
                "source_message_id": "m2",
            }
        ),
    ]
    summary = summarize(tickets, existing_ids={"BMS123456789"})
    assert summary.total == 3
    assert summary.complete == 2
    assert summary.incomplete == 1
    assert summary.would_create == 1
    assert summary.would_update == 1
    assert summary.would_skip == 1
    assert (
        summary.would_create
        + summary.would_update
        + summary.would_skip
        == summary.total
    )
    printed = summary.lines()
    assert printed.startswith("Dry-run summary")
    assert "Show_Date_Text__c" in printed
    assert "Booking_Id__c" in printed


def test_committed_tickets_json_dry_run_counts():
    path = Path(__file__).resolve().parents[2] / "react-app" / "public" / "tickets.json"
    tickets = json.loads(path.read_text())
    summary = summarize(tickets)
    assert summary.total == len(tickets)
    assert summary.complete + summary.incomplete == summary.total
    assert (
        summary.would_create + summary.would_update + summary.would_skip
        == summary.total
    )
    assert summary.incomplete == sum(1 for t in tickets if not t.get("complete"))
    assert "Show_Date_Text__c" in summary.lines()
