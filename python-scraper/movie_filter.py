"""
Movie-vs-event filter.

Movie markers: Cinema, Screen, IMAX, PVR, INOX, Cinepolis.
Event markers: Concert, Match, Comedy, Theatre, Festival.
Skip if event score wins. One keyword is not a decision.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple

MOVIE_MARKERS = ("Cinema", "Screen", "IMAX", "PVR", "INOX", "Cinepolis")
EVENT_MARKERS = ("Concert", "Match", "Comedy", "Theatre", "Festival")


def _count_markers(text: str, markers: Tuple[str, ...]) -> int:
    haystack = text or ""
    score = 0
    for marker in markers:
        pattern = r"\b" + re.escape(marker) + r"\b"
        hits = re.findall(pattern, haystack, flags=re.IGNORECASE)
        score += len(hits)
    return score


def score_email(text: str) -> Dict[str, int]:
    movie = _count_markers(text, MOVIE_MARKERS)
    event = _count_markers(text, EVENT_MARKERS)
    return {"movie": movie, "event": event, "total": movie + event}


def is_movie_booking(text: str) -> bool:
    """
    Keep the email unless event markers clearly win.

    A single keyword is not a decision either way, so a lone "Concert"
    does not skip and a lone "PVR" does not force-keep over stronger
    event evidence — but with only one keyword total, we keep and let
    parse decide completeness.
    """
    scores = score_email(text)
    if scores["total"] <= 1:
        return True
    if scores["event"] > scores["movie"]:
        return False
    return True
