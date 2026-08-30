"""
Ollama enrichment: cinema_name, city, blurb only.

llama3.1:8b or qwen2.5:7b-instruct, temperature 0, strict JSON.
Validate then merge. Discard on failure. Never touches factual fields.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

import httpx

from config import settings

ALLOWED_MODELS = ("llama3.1:8b", "qwen2.5:7b-instruct")
ALLOWED_FIELDS = ("cinema_name", "city", "blurb")


class OllamaClient:
    def __init__(
        self,
        url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_ms: Optional[int] = None,
    ):
        self.url = (url or settings.ollama_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout_s = (timeout_ms or settings.ollama_timeout_ms) / 1000
        if self.model not in ALLOWED_MODELS:
            # Keep going if a close tag is present (e.g. llama3.1:8b-instruct)
            if not any(self.model.startswith(m.split(":")[0]) for m in ALLOWED_MODELS):
                self.model = "llama3.1:8b"

    def available(self) -> bool:
        try:
            response = httpx.get(f"{self.url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def enrich(self, ticket: Dict[str, Any]) -> Optional[Dict[str, str]]:
        prompt = (
            "Return ONLY JSON with keys cinema_name, city, blurb. "
            "cinema_name is the cinema brand and mall, without the city. "
            "city is the Indian city if present. "
            "blurb is one short sentence about seeing this movie. "
            "Do not invent a booking id, movie title, date, seats, or amount.\n\n"
            f"cinema_raw: {ticket.get('cinema_raw')}\n"
            f"movie_title: {ticket.get('movie_title')}\n"
            f"show_date_raw: {ticket.get('show_date_raw')}\n"
        )
        try:
            response = httpx.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0},
                },
                timeout=self.timeout_s,
            )
            response.raise_for_status()
            raw = response.json().get("response") or ""
            parsed = _parse_json(raw)
            if not parsed:
                return None
            cleaned = {}
            for field in ALLOWED_FIELDS:
                value = parsed.get(field)
                if isinstance(value, str) and value.strip():
                    cleaned[field] = value.strip()
            return cleaned or None
        except (httpx.HTTPError, json.JSONDecodeError, ValueError, KeyError):
            return None


def _parse_json(raw: str) -> Optional[Dict[str, Any]]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                return None
        return None
