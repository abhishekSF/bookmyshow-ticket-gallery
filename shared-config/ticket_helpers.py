"""
Shared ticket contract: record shape, IST dates, completeness, Salesforce payload.

Three locks:
1. show_date_iso, when set, must include +05:30.
2. Never infer year from Gmail received time. Partial dates stay raw-only.
3. Salesforce write never maps complete: false (enforced in python-scraper).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

IST_OFFSET = "+05:30"
CATEGORY_MOVIE = "Movie"
MISSING_BOOKING_PREFIX = "BMS_MISSING_"

TICKET_FIELDS = (
    "booking_id",
    "movie_title",
    "cinema_raw",
    "cinema_name",
    "city",
    "show_date_raw",
    "show_date_iso",
    "seats",
    "seat_display",
    "quantity",
    "amount",
    "currency",
    "poster_url",
    "poster_source",
    "blurb",
    "source_message_id",
    "complete",
    "missing_fields",
)

COMPLETE_REQUIRED = ("booking_id", "movie_title", "show_date_raw")

# Ollama may only merge these. Everything else is factual / parser-owned.
OLLAMA_FIELDS = ("cinema_name", "city", "blurb")

INDIAN_CITIES = {
    "ahmedabad",
    "bengaluru",
    "bangalore",
    "bhopal",
    "chandigarh",
    "chennai",
    "coimbatore",
    "delhi",
    "noida",
    "gurugram",
    "gurgaon",
    "hyderabad",
    "indore",
    "jaipur",
    "kochi",
    "kolkata",
    "lucknow",
    "mumbai",
    "nagpur",
    "pune",
    "surat",
    "thiruvananthapuram",
    "vadodara",
    "visakhapatnam",
    "new delhi",
    "navi mumbai",
}

INDIAN_VENUE_MARKERS = {
    "pvr",
    "inox",
    "cinepolis",
    "carnival cinemas",
    "miraj",
    "movietime",
    "spi cinemas",
    "fun cinemas",
    "wave cinemas",
    "mukta a2",
    "pvr inox",
}


class IncompleteTicketError(ValueError):
    """Raised when a Salesforce payload is requested for complete: false."""


def empty_ticket(source_message_id: Optional[str] = None) -> Dict[str, Any]:
    return {
        "booking_id": None,
        "movie_title": None,
        "cinema_raw": None,
        "cinema_name": None,
        "city": None,
        "show_date_raw": None,
        "show_date_iso": None,
        "seats": [],
        "seat_display": None,
        "quantity": None,
        "amount": None,
        "currency": None,
        "poster_url": None,
        "poster_source": None,
        "blurb": None,
        "source_message_id": source_message_id,
        "complete": False,
        "missing_fields": [],
    }


def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def placeholder_booking_id(source_message_id: str) -> str:
    return f"{MISSING_BOOKING_PREFIX}{source_message_id}"


def is_placeholder_booking_id(booking_id: Optional[str]) -> bool:
    return bool(booking_id) and str(booking_id).startswith(MISSING_BOOKING_PREFIX)


def apply_missing_booking_id(ticket: Dict[str, Any]) -> Dict[str, Any]:
    source_id = ticket.get("source_message_id") or "unknown"
    if not ticket.get("booking_id"):
        ticket["booking_id"] = placeholder_booking_id(str(source_id))
    return ticket


def seat_display_from(seats: Optional[Sequence[str]]) -> Optional[str]:
    if not seats:
        return None
    cleaned = [clean_text(s) for s in seats if clean_text(s)]
    return ", ".join(cleaned) if cleaned else None


def finalize_ticket(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """Fill derived fields and completeness. Does not invent dates or years."""
    apply_missing_booking_id(ticket)
    seats = ticket.get("seats") or []
    if isinstance(seats, str):
        seats = [s.strip() for s in re.split(r"[,;]+", seats) if s.strip()]
        ticket["seats"] = seats
    ticket["seat_display"] = ticket.get("seat_display") or seat_display_from(seats)
    if ticket.get("quantity") is None and seats:
        ticket["quantity"] = len(seats)

    iso = ticket.get("show_date_iso")
    if iso:
        if IST_OFFSET not in str(iso):
            raise ValueError(
                f"show_date_iso must include {IST_OFFSET}; got {iso!r}"
            )
        ticket["show_date_iso"] = str(iso)
    else:
        ticket["show_date_iso"] = None

    missing: List[str] = []
    booking_id = ticket.get("booking_id")
    if not booking_id or is_placeholder_booking_id(booking_id):
        missing.append("booking_id")
    if not clean_text(ticket.get("movie_title")):
        missing.append("movie_title")
    if not clean_text(ticket.get("show_date_raw")):
        missing.append("show_date_raw")

    ticket["missing_fields"] = missing
    ticket["complete"] = len(missing) == 0
    return ticket


def clearly_indian_venue(cinema_raw: Optional[str], city: Optional[str] = None) -> bool:
    haystack = " ".join(
        part for part in (cinema_raw, city) if part
    ).lower()
    if not haystack:
        return False
    if any(city_name in haystack for city_name in INDIAN_CITIES):
        return True
    if any(marker in haystack for marker in INDIAN_VENUE_MARKERS):
        return True
    if re.search(r"\bindia\b", haystack):
        return True
    return False


_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_TIME_RE = re.compile(
    r"\b(\d{1,2})(?::(\d{2}))?\s*([AaPp][Mm])\b|\b([01]?\d|2[0-3]):([0-5]\d)\b"
)


def _has_explicit_year(raw: str) -> bool:
    return bool(_YEAR_RE.search(raw or ""))


def _has_time(raw: str) -> bool:
    return bool(_TIME_RE.search(raw or ""))


def parse_show_date_iso(
    show_date_raw: Optional[str],
    cinema_raw: Optional[str] = None,
    city: Optional[str] = None,
    received_at: Any = None,
) -> Optional[str]:
    """
    Convert a confident Indian movie show datetime to ISO-8601 with +05:30.

    received_at is accepted so callers can pass Gmail internalDate. It is
    ignored. Missing year, missing time, or a venue that is not clearly
    Indian: return None and keep show_date_raw only.
    """
    del received_at  # lock 2: Gmail received time is never a year source
    raw = clean_text(show_date_raw)
    if not raw:
        return None
    if not _has_explicit_year(raw):
        return None
    if not _has_time(raw):
        return None
    if not clearly_indian_venue(cinema_raw, city):
        return None

    try:
        from dateutil import parser as dateutil_parser
    except ImportError as exc:
        raise RuntimeError("python-dateutil is required for show_date_iso") from exc

    year_in_raw = int(_YEAR_RE.search(raw).group(1))
    # Sentinel default so a missing year cannot silently become "today" or
    # Gmail received time. dateutil fills absent fields from default=.
    sentinel = datetime(1900, 1, 1, 0, 0, 0)
    try:
        parsed = dateutil_parser.parse(raw, fuzzy=True, default=sentinel)
    except (ValueError, OverflowError):
        return None

    if parsed is None or parsed.year == 1900:
        return None
    if parsed.year != year_in_raw:
        return None
    if parsed.year < 2000 or parsed.year > 2100:
        return None

    iso = (
        f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}"
        f"T{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
        f"{IST_OFFSET}"
    )
    if IST_OFFSET not in iso:
        raise ValueError("internal date format dropped IST offset")
    return iso


def assert_iso_offset(iso: Optional[str]) -> None:
    if iso is None:
        return
    if IST_OFFSET not in iso:
        raise ValueError(f"show_date_iso missing {IST_OFFSET}: {iso!r}")


def ticket_to_salesforce(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a tickets.json record to Ticket__c fields.

    Raises IncompleteTicketError on complete: false. Show_Date_Text__c is
    always set. Show_Date__c is omitted unless show_date_iso is a confident IST
    datetime.
    """
    if not ticket.get("complete"):
        raise IncompleteTicketError(
            "cannot push complete: false; --confirm does not override"
        )
    if is_placeholder_booking_id(ticket.get("booking_id")):
        raise IncompleteTicketError(
            "cannot push placeholder booking id BMS_MISSING_*"
        )

    assert_iso_offset(ticket.get("show_date_iso"))

    payload: Dict[str, Any] = {
        "Event_Name__c": ticket.get("movie_title"),
        "Venue__c": ticket.get("cinema_name") or ticket.get("cinema_raw"),
        "Venue_City__c": ticket.get("city"),
        "Show_Date_Text__c": ticket.get("show_date_raw") or "",
        "Seats__c": ticket.get("seat_display")
        or seat_display_from(ticket.get("seats") or []),
        "Quantity__c": ticket.get("quantity"),
        "Booking_Id__c": ticket.get("booking_id"),
        "Amount__c": ticket.get("amount"),
        "Currency__c": ticket.get("currency"),
        "Poster_URL__c": ticket.get("poster_url"),
        "Source_Message_Id__c": ticket.get("source_message_id"),
        "Category__c": CATEGORY_MOVIE,
    }

    iso = ticket.get("show_date_iso")
    if iso:
        payload["Show_Date__c"] = iso
    # else leave Show_Date__c out entirely rather than guess

    return {key: value for key, value in payload.items() if value is not None}


def sample_payload_fields() -> List[str]:
    return [
        "Event_Name__c",
        "Venue__c",
        "Show_Date__c",
        "Show_Date_Text__c",
        "Seats__c",
        "Booking_Id__c",
        "Amount__c",
        "Currency__c",
        "Category__c",
    ]


def merge_ollama_enrichment(
    ticket: Dict[str, Any], enrichment: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Copy cinema_name, city, blurb only. Discard anything else."""
    if not enrichment or not isinstance(enrichment, dict):
        return ticket
    for field in OLLAMA_FIELDS:
        value = enrichment.get(field)
        if value is None:
            continue
        text = clean_text(str(value))
        if text:
            ticket[field] = text
    return ticket


def strip_for_tableau(tickets: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Drop booking IDs, exact seats, and Gmail message IDs."""
    rows = []
    for ticket in tickets:
        iso = ticket.get("show_date_iso")
        year = None
        month = None
        if iso and len(iso) >= 7:
            year = iso[:4]
            month = iso[:7]
        elif ticket.get("show_date_raw"):
            year_match = _YEAR_RE.search(ticket["show_date_raw"])
            if year_match:
                year = year_match.group(1)
        rows.append(
            {
                "movie_title": ticket.get("movie_title"),
                "cinema_name": ticket.get("cinema_name") or ticket.get("cinema_raw"),
                "city": ticket.get("city"),
                "year": year,
                "month": month,
                "quantity": ticket.get("quantity"),
                "amount": ticket.get("amount"),
                "currency": ticket.get("currency"),
                "poster_url": ticket.get("poster_url"),
            }
        )
    return rows


def extract_year_from_iso_or_raw(ticket: Dict[str, Any]) -> Optional[str]:
    iso = ticket.get("show_date_iso")
    if iso and _YEAR_RE.search(iso):
        return iso[:4]
    raw = ticket.get("show_date_raw") or ""
    match = _YEAR_RE.search(raw)
    return match.group(1) if match else None


def format_show_datetime(date: str, time: str = "") -> str:
    """Display helper. Does not invent an ISO datetime."""
    parts = [clean_text(date), clean_text(time)]
    return ", ".join(p for p in parts if p) or ""
