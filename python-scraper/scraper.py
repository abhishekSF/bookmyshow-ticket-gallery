"""
Deterministic BookMyShow movie-ticket parse. No Ollama.

Sets complete and missing_fields. Date ISO is +05:30 or null.
Never uses Gmail received time as a year.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

SHARED = Path(__file__).resolve().parent.parent / "shared-config"
sys.path.insert(0, str(SHARED))

from ticket_helpers import (  # noqa: E402
    clean_text,
    empty_ticket,
    finalize_ticket,
    parse_show_date_iso,
)

BOOKING_ID_PATTERNS = [
    re.compile(
        r"\b(?:Booking\s*(?:ID|Id|Number|Ref(?:erence)?)|BMS\s*ID)\s*[:.#-]*\s*([A-Z0-9]{6,20})\b",
        re.I,
    ),
    re.compile(r"\b(BMS[A-Z0-9]{6,18})\b", re.I),
]

MOVIE_TITLE_PATTERNS = [
    re.compile(r"(?:Movie|Film|Show\s*Name|Event)\s*[:\-]\s*([^\n<]{2,80})", re.I),
    re.compile(r"(?:you(?:'ve| have)?\s+booked|booking\s+for)\s*[:\-]?\s*([^\n<]{2,80})", re.I),
]

CINEMA_PATTERNS = [
    re.compile(
        r"(?:Cinema|Theatre|Theater|Venue|Location)\s*[:\-]\s*([^\n<]{2,120})",
        re.I,
    ),
]

DATE_PATTERNS = [
    re.compile(
        r"(?:Show\s*Date|Date\s*&?\s*Time|Date|Show(?:time)?)\s*[:\-]\s*([^\n<]{6,80})",
        re.I,
    ),
    re.compile(
        r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+\d{1,2}\s+"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
        r"(?:\s+\d{4})?(?:\s*,?\s*\d{1,2}:\d{2}\s*(?:[APap][Mm])?)?",
        re.I,
    ),
]

SEAT_PATTERNS = [
    re.compile(r"(?:Seats?|Seat\s*No\.?)\s*[:\-]\s*([^\n<]+)", re.I),
]

AMOUNT_PATTERNS = [
    re.compile(r"(?:₹|INR|Rs\.?)\s*([0-9]{2,6}(?:,[0-9]{2,3})*(?:\.\d{1,2})?)", re.I),
    re.compile(
        r"(?:Amount|Total|Paid|Grand\s*Total)\s*[:\-]?\s*(?:₹|INR|Rs\.?)?\s*"
        r"([0-9]{2,6}(?:,[0-9]{3})*(?:\.\d{1,2})?)",
        re.I,
    ),
]


def _plain_text(email: Dict[str, Any]) -> str:
    html = email.get("html") or ""
    text = email.get("text") or ""
    if html:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        html_text = soup.get_text("\n", strip=True)
    else:
        html_text = ""
    headers = email.get("headers") or {}
    return "\n".join(
        part
        for part in (
            headers.get("subject", ""),
            text,
            html_text,
            email.get("snippet") or "",
        )
        if part
    )


def _first_match(patterns: List[re.Pattern], text: str) -> Optional[str]:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            value = match.group(1) if match.lastindex else match.group(0)
            value = clean_text(value)
            value = re.split(r"\s{2,}|\n", value)[0].strip(" .:-")
            if value:
                return value
    return None


def _parse_seats(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return re.findall(r"\b([A-Z]{1,2}\d{1,3})\b", raw.upper())


def _parse_amount(raw: Optional[str]) -> Optional[float]:
    if not raw:
        return None
    digits = raw.replace(",", "")
    try:
        return float(digits)
    except ValueError:
        return None


def parse_email(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse one stored Gmail message dict into a tickets.json record.

    email.internal_date / headers.date are available but must not be used
    as a year for show_date_iso.
    """
    source_id = str(email.get("id") or email.get("source_message_id") or "unknown")
    ticket = empty_ticket(source_id)
    text = _plain_text(email)

    booking_id = _first_match(BOOKING_ID_PATTERNS, text)
    if booking_id:
        ticket["booking_id"] = booking_id.upper()

    ticket["movie_title"] = _first_match(MOVIE_TITLE_PATTERNS, text)
    cinema = _first_match(CINEMA_PATTERNS, text)
    ticket["cinema_raw"] = cinema
    if cinema:
        bits = [clean_text(b) for b in cinema.split(",") if clean_text(b)]
        if bits:
            ticket["cinema_name"] = bits[0]
        if len(bits) >= 2:
            ticket["city"] = bits[-1]

    show_raw = _first_match(DATE_PATTERNS, text)
    ticket["show_date_raw"] = show_raw
    # Lock 2: pass received time only to prove it is ignored.
    ticket["show_date_iso"] = parse_show_date_iso(
        show_raw,
        cinema_raw=ticket.get("cinema_raw"),
        city=ticket.get("city"),
        received_at=email.get("internal_date") or (email.get("headers") or {}).get("date"),
    )

    seats = _parse_seats(_first_match(SEAT_PATTERNS, text))
    ticket["seats"] = seats

    amount = _parse_amount(_first_match(AMOUNT_PATTERNS, text))
    if amount is not None:
        ticket["amount"] = amount
        ticket["currency"] = "INR"

    return finalize_ticket(ticket)


def parse_emails(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [parse_email(email) for email in emails]
