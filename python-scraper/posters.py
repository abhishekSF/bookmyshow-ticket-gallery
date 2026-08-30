"""TMDb poster lookup by movie title. Misses stay null; gallery draws fallback art."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx

from config import settings


def lookup_poster(title: Optional[str], api_key: Optional[str] = None) -> Dict[str, Optional[str]]:
    api_key = api_key if api_key is not None else settings.tmdb_api_key
    if not title or not api_key or not settings.tmdb_enable:
        return {"poster_url": None, "poster_source": "fallback"}
    params = urlencode({"api_key": api_key, "query": title, "include_adult": "false"})
    url = f"https://api.themoviedb.org/3/search/movie?{params}"
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        results = response.json().get("results") or []
        for movie in results:
            path = movie.get("poster_path")
            if path:
                return {
                    "poster_url": f"https://image.tmdb.org/t/p/w500{path}",
                    "poster_source": "tmdb",
                }
    except httpx.HTTPError:
        pass
    return {"poster_url": None, "poster_source": "fallback"}


def apply_poster(ticket: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    if ticket.get("poster_url") and ticket.get("poster_source") == "tmdb":
        return ticket
    result = lookup_poster(ticket.get("movie_title"), api_key=api_key)
    ticket["poster_url"] = result["poster_url"]
    ticket["poster_source"] = result["poster_source"]
    return ticket
