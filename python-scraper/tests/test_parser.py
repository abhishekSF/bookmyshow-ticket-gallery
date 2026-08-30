from scraper import parse_email
from ticket_helpers import finalize_ticket, merge_ollama_enrichment


MOVIE_HTML = """
<html><body>
<h1>Booking Confirmation</h1>
<p>Booking ID: BMS123456789</p>
<p>Movie: Dune: Part Two</p>
<p>Cinema: PVR Forum Mall, Koramangala, Bengaluru</p>
<p>Date: Sat, 15 Mar 2026, 7:30 PM</p>
<p>Seats: G12, G13</p>
<p>Amount: ₹980</p>
<p>Screen 5 IMAX</p>
</body></html>
"""

PARTIAL_DATE_HTML = """
<html><body>
<p>Booking ID: BMS555</p>
<p>Movie: Jawan</p>
<p>Cinema: PVR Powai, Mumbai</p>
<p>Date: Sat, 15 Mar, 7:30 PM</p>
<p>Screen 3</p>
</body></html>
"""


def test_parse_complete_movie_email():
    ticket = parse_email(
        {
            "id": "msg-dune",
            "internal_date": "1700000000000",
            "headers": {"subject": "Booking confirmation"},
            "html": MOVIE_HTML,
            "text": "",
        }
    )
    assert ticket["booking_id"] == "BMS123456789"
    assert ticket["movie_title"] == "Dune: Part Two"
    assert "PVR Forum Mall" in (ticket["cinema_raw"] or "")
    assert ticket["show_date_iso"] == "2026-03-15T19:30:00+05:30"
    assert ticket["seats"] == ["G12", "G13"]
    assert ticket["amount"] == 980
    assert ticket["currency"] == "INR"
    assert ticket["complete"] is True
    assert ticket["missing_fields"] == []


def test_parse_does_not_use_gmail_internal_date_as_year():
    ticket = parse_email(
        {
            "id": "msg-jawan",
            "internal_date": "1735689600000",
            "headers": {"date": "Tue, 31 Dec 2024 10:00:00 +0000"},
            "html": PARTIAL_DATE_HTML,
            "text": "",
        }
    )
    assert ticket["show_date_raw"]
    assert ticket["show_date_iso"] is None
    assert "2024" not in (ticket["show_date_iso"] or "")


def test_missing_booking_id_placeholder():
    ticket = parse_email(
        {
            "id": "abc123",
            "html": "<p>Movie: Dune: Part Two</p><p>Date: Sat, 15 Mar 2026, 7:30 PM</p>"
            "<p>Cinema: PVR Forum Mall, Bengaluru</p><p>Screen 1</p>",
            "text": "",
            "headers": {},
        }
    )
    assert ticket["booking_id"] == "BMS_MISSING_abc123"
    assert ticket["complete"] is False
    assert "booking_id" in ticket["missing_fields"]


def test_ollama_cannot_overwrite_factual_fields():
    ticket = parse_email(
        {
            "id": "msg-dune",
            "html": MOVIE_HTML,
            "text": "",
            "headers": {},
        }
    )
    poisoned = merge_ollama_enrichment(
        ticket,
        {
            "cinema_name": "PVR Forum Mall",
            "city": "Bengaluru",
            "blurb": "Spice and sand.",
            "booking_id": "HACKED",
            "movie_title": "Wrong",
            "show_date_iso": "1999-01-01T00:00:00Z",
            "amount": 1,
        },
    )
    poisoned = finalize_ticket(poisoned)
    assert poisoned["booking_id"] == "BMS123456789"
    assert poisoned["movie_title"] == "Dune: Part Two"
    assert poisoned["show_date_iso"] == "2026-03-15T19:30:00+05:30"
    assert poisoned["amount"] == 980
    assert poisoned["city"] == "Bengaluru"
    assert poisoned["blurb"] == "Spice and sand."
