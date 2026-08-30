"""
Ollama client for local LLM communication.
Provides offline-capable LLM calls for text cleanup/enrichment only.
NEVER uses LLM for primary extraction (deterministic parsing first).
"""

import httpx
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from config import settings


# Strict response model - LLM must return this exact structure
class EnrichmentResponse(BaseModel):
    """Standard enrichment response structure for all enrichment types."""
    original_value: str = Field(..., description="Original extracted value")
    cleaned_value: Optional[str] = Field(None, description="Cleaned value after processing")
    category: Optional[str] = Field(None, description="Inferred category: movie, concert, sports, comedy, play, theatre, uncategorized")
    blurb: Optional[str] = Field(None, max_length=150, description="One-line blurb about the event")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in LLM's suggestions (0-1)")
    suggestions: Optional[List[Dict[str, str]]] = Field(default=None, description="Alternative suggestions")


class PosterResponse(BaseModel):
    """TMDb poster lookup response."""
    title: str
    poster_url: Optional[str] = None
    fallback_url: Optional[str] = None
    match_type: str = "exact"  # exact, partial, no_match


class OllamaClient:
    """
    Client for interacting with local Ollama instances.
    Designed for: text cleanup, category inference, blurb generation.
    """
    
    def __init__(self, url: str = None, model: str = None, timeout_ms: int = 60000):
        """Initialize Ollama client."""
        self.url = url or settings.ollama_url
        self.model = model or settings.ollama_model
        self.timeout_s = timeout_ms / 1000  # Convert to seconds
        self.enable = settings.ollama_enable
        self.client = None
    
    def connect(self) -> bool:
        """Establish connection to Ollama. Returns True if successful."""
        if not self.enable:
            return False
        
        try:
            self.client = httpx.AsyncClient(
                base_url=self.url,
                timeout=httpx.Timeout(10.0)
            )
            # Test connection
            response = self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def cleanup_venue(self, venue_name: str) -> Dict[str, Any]:
        """
        Clean up inconsistent venue name strings.
        Remap common variations to standard names.
        """
        if not self.enable or not self.client:
            return {"original": venue_name, "cleaned": venue_name, "confidence": 0.0}
        
        prompt = f"""
        Clean up the following venue name by removing:
        - Extra spaces, hyphens at ends, repeated characters
        - Suffixes like "India", "Delhi", "National", "International"
        - Common phrases like "at", "in", "The", "A", "An"
        
        Return ONLY valid JSON in this exact structure (no markdown, no extra text):
        {{
            "original_value": "<original venue name>",
            "cleaned_value": "<cleaned venue name>",
            "confidence_score": <number from 0 to 1>
        }}
        
        Keep the venue name recognizable but concise.
        """
        
        response = await self.client.post(
            "/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=self.timeout_s
        )
        
        content = response.json()
        return self._parse_llm_response(content.get("response", ""), "venue cleanup")
    
    async def infer_category(self, event_title: str) -> Dict[str, Any]:
        """
        Infer genre/category from event title.
        Returns: movie, concert, sports, comedy, play, theatre, or uncategorized.
        """
        if not self.enable or not self.client:
            return {"original": event_title, "category": "uncategorized", "confidence": 0.0}
        
        prompt = f"""
        Infer the category for the following event title.
        Choose from: movie, concert, sports, comedy, play, theatre, uncategorized.
        
        Return ONLY valid JSON in this exact structure (no markdown, no extra text):
        {{
            "original_value": "<original event title>",
            "category": "<one of the above categories>",
            "confidence_score": <number from 0 to 1>
        }}
        
        Use these heuristics:
        - Movies: Has actor names, studio references, theatrical release dates
        - Concerts: Artist + "concert" or "live", or musician-specific terms
        - Sports: Team names, league references, athlete names
        - Comedy: "Stand-up", "Comedy night", comedian names
        - Play/Theatre: Playwright names, theater productions, "play" in title
        - Uncategorized: When unable to determine
        
        Event title: {event_title}
        """
        
        response = await self.client.post(
            "/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=self.timeout_s
        )
        
        content = response.json()
        return self._parse_llm_response(content.get("response", ""), "category inference")
    
    async def generate_blurb(self, event_title: str, date: str, venue: str = None) -> Dict[str, Any]:
        """
        Generate a one-line blurb about the event.
        """
        if not self.enable or not self.client:
            return {"original": "", "blurb": f"Event on {date}" if date else "", "confidence": 1.0}
        
        prompt = f"""
        Write a one-line blurb (max 15 words) about this event:
        - Mention the type of event
        - Include date
        - Include venue if provided
        
        Return ONLY valid JSON in this exact structure (no markdown, no extra text):
        {{
            "original_value": "<original title>",
            "blurb": "<one line blurb, max 150 chars>",
            "confidence_score": <number from 0 to 1>
        }}
        
        Event details:
        Title: {event_title}
        Date: {date}
        Venue: {venue}
        """
        
        response = await self.client.post(
            "/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=self.timeout_s
        )
        
        content = response.json()
        return self._parse_llm_response(content.get("response", ""), "blurb generation")
    
    async def resolve_ambiguous(self, field_name: str, low_confidence_value: str, 
                                alternative_value: str) -> Dict[str, Any]:
        """
        Help resolve ambiguous field extraction when regex confidence is low.
        Returns recommendation based on which value makes more sense.
        """
        if not self.enable or not self.client:
            # Default to alternative if not confident
            return {"original": low_confidence_value, "cleaned_value": alternative_value, "confidence": 0.5}
        
        prompt = f"""
        Compare two extracted values for {field_name} and recommend which is correct:
        Value 1 (lower confidence): {low_confidence_value}
        Value 2 (higher confidence): {alternative_value}
        
        Return ONLY valid JSON in this exact structure (no markdown, no extra text):
        {{
            "original_value": "<the value we were given>",
            "cleaned_value": "<recommended value or original>",
            "confidence_score": <1.0 if alternative is clearly better, 0.5 if unclear>
        }}
        
        Context: For structured booking confirmations, prefer the more complete/standardized value.
        For event dates, prefer the more specific one.
        For amounts, prefer the more detailed one.
        
        Field: {field_name}
        """
        
        response = await self.client.post(
            "/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=self.timeout_s
        )
        
        content = response.json()
        return self._parse_llm_response(content.get("response", ""), "ambiguous resolution")
    
    async def fetch_possibles(self, category: str) -> List[Dict[str, str]]:
        """
        Get alternative/suggested values for a category.
        """
        if not self.enable or not self.client:
            return []
        
        prompt = f"""
        Give me 3-5 alternative examples of the category: {category}.
        
        Return ONLY a JSON array in this exact structure (no markdown, no extra text):
        [
            {{ "suggestion_1": "example value 1", "suggestion_2": "example value 2" }},
            {{ "suggestion_1": "example value 1" }},
            ...
        ]
        
        Category: {category}
        """
        
        response = await self.client.post(
            "/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=self.timeout_s
        )
        
        content = response.json()
        
        try:
            data = json.loads(content.get("response", "[]"))
            if isinstance(data, list):
                return data
            return [data] if data else []
        except json.JSONDecodeError:
            return []
    
    def _parse_llm_response(self, raw_text: str, response_type: str) -> Dict[str, Any]:
        """Parse LLM response, handling potential JSON wrapping issues."""
        # Try to extract JSON from response
        json_match = self._extract_json(raw_text)
        
        if not json_match:
            # Return generic response if parsing failed
            return self._get_generic_response(raw_text, response_type)
        
        try:
            data = json.loads(json_match)
            return EnrichmentResponse(**data).model_dump()
        except Exception:
            return {"error": f"Failed to parse {response_type} response", "raw": raw_text}
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from text that may have markdown formatting."""
        # Remove markdown code blocks
        text = text.replace("```json", "").replace("```", "").replace("```json ", "")
        
        # Find first { and last }
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return text[start:end+1]
        except:
            pass
        return None
    
    def _get_generic_response(self, raw_text: str, response_type: str) -> Dict[str, Any]:
        """Fallback response when parsing fails."""
        return {
            "original_value": raw_text[:50] if raw_text else "",
            "error": f"Failed to parse {response_type} response - LLM did not return valid JSON",
            "confidence_score": 0.0
        }


class PosterClient:
    """
    Client for TMDb API poster lookups.
    Fallback for movie poster images when email has no poster_url.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize Poster client."""
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.enable = settings.tmdb_enable
        self.enabled = self.api_key and self.enable
    
    def fetch_poster(self, title: str) -> Dict[str, Any]:
        """
        Fetch poster URL from TMDb for given title.
        Returns poster URL or fallback image if no exact match.
        """
        if not self.enabled:
            return {
                "title": title,
                "poster_url": None,
                "fallback_url": f"https://placehold.co/300x450/333/FFF?text={title.replace(' ', '+')[:20]}",
                "match_type": "no_match"
            }
        
        headers = {"accept-language": "en-US,en", "Authorization": f"api_key={self.api_key}"}
        
        # Search for movie by title
        params = {
            "api_key": self.api_key,
            "language": "en-US",
            "page": 1,
            "query": title,
            "append_to_response": "profiles"
        }
        
        try:
            response = httpx.get(
                f"{self.base_url}/search/movie",
                params=params,
                headers=headers,
                timeout=10.0
            )
            
            data = response.json()
            results = data.get("results", [])
            
            if results:
                # Get first movie result
                movie = results[0]
                
                # Check if profile image exists (indicates it's a real movie)
                if movie.get("poster_path"):
                    return {
                        "title": title,
                        "poster_url": f"https://image.tmdb.org/t/p/w300{movie['poster_path']}",
                        "fallback_url": None,
                        "match_type": "exact"
                    }
                elif results[0].get("title") in results:
                    return {
                        "title": title,
                        "poster_url": f"https://image.tmdb.org/t/p/w300{results[1]['poster_path'] if len(results) > 1 else results[0]['poster_path']}",
                        "fallback_url": None,
                        "match_type": "partial"
                    }
            
            return {
                "title": title,
                "poster_url": None,
                "fallback_url": f"https://placehold.co/300x450/333/FFF?text={title.replace(' ', '+')[:20]}",
                "match_type": "no_match"
            }
            
        except Exception:
            return {
                "title": title,
                "poster_url": None,
                "fallback_url": f"https://placehold.co/300x450/333/FFF?text={title.replace(' ', '+')[:20]}",
                "match_type": "error"
            }


async def main():
    """Test Ollama client connectivity and basic functionality."""
    print("\n=== Testing Ollama Client ===\n")
    
    client = OllamaClient()
    if client.connect():
        print("✓ Ollama connection successful!")
        print(f"  Model: {client.model}")
        
        # Test cleanup
        test_venues = ["Alia Bhatt India", "Sri Venkateswara Deluxe, India", "Urban Multiplex"]
        for venue in test_venues:
            result = await client.cleanup_venue(venue)
            print(f"  Venue: {venue}")
            print(f"    → {result}")
            print()
    else:
        print("✗ Ollama not running or unavailable")
        print("  Start Ollama: 'ollama serve' or check if llama3.1:8b is pulled")
        print()
    
    print("\n=== Testing TMDb Poster Client ===\n")
    
    poster_client = PosterClient()
    test_titles = ["Dangal", "3 Idiots", "Jawan"]
    for title in test_titles:
        result = poster_client.fetch_poster(title)
        print(f"  Title: {title}")
        print(f"    Poster: {result['poster_url'][:50]}..." if result['poster_url'] else "    Poster: N/A (fallback used)")
        print(f"    Match: {result['match_type']}")
        print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())