"""
Gmail API client for fetching and parsing BookMyShow booking confirmation emails.
Handles OAuth authentication and email extraction.
"""

import base64
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup
import re
import os
from typing import Dict, List, Optional, Any
import json


# Gmail API scopes - readonly for personal use
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Search query for BookMyShow emails
BOOKMYSHOW_EMAIL_PATTERNS = [
    "noreply@bookmyshow.com",
    "bookmyshow.com",
    "books@bookmyshow.com",
    "tickets@bookmyshow.com",
]

# Subject keywords that indicate a booking confirmation
BOOKING_SUBJECT_KEYWORDS = [
    "booking confirmation",
    "booking successful",
    "booking id",
    "seat booking",
    "reservation confirmation",
    "ticket booking",
    "Your booking is confirmed",
]

# Template type detection patterns
TEMPLATE_PATTERNS = {
    "movie": [
        r"(?:movie|film|cinema|theatrical)",
        r"admission ticket",
        r"screen\s*\d+",
        r"lead\s+role[s]?\s*[:(]\s*\w+",  # "Lead roles: Actor Name, Actor Name"
    ],
    "event": [
        r"(?:live concert|live event|live show)",
        r"entry ticket",
        r"venue",
        r"artist|performer",
    ],
    "sports": [
        r"match|game|fixture",
        r"team",
        r"team1|team2|team A|team B",
        r"ticket for",
    ],
    "comedy": [
        r"stand-up",
        r"comedy night",
        r"comedian",
        r"comedy show",
    ],
    "play": [
        r"(?:play|theatre|musical)",
        r"actor|actress|stage",
        r"production",
    ],
}


class GmailAPIError(Exception):
    """Custom exception for Gmail API errors."""
    pass


class BookingRecord:
    """
    Represents a parsed booking record from an email.
    """
    def __init__(self):
        self.booking_id: Optional[str] = None
        self.event_name: Optional[str] = None
        self.venue: Optional[str] = None
        self.show_date: Optional[str] = None
        self.show_time: Optional[str] = None
        self.seats: Optional[str] = None
        self.amount_paid: Optional[float] = None
        self.poster_url: Optional[str] = None
        self.category: Optional[str] = None  # movie, concert, sports, comedy, play, theatre, uncategorized
        self.confidence_score: float = 0.0  # 0-100% confidence in extraction
        self.raw_email_data: Optional[Dict] = None  # Store raw parsed data for debugging


class BookMyShowEmailParser:
    """
    Parser for BookMyShow booking confirmation emails.
    Uses regex and BeautifulSoup for deterministic extraction.
    Routes low-confidence extractions to Ollama for cleanup.
    """
    
    @staticmethod
    def extract_text_from_html(html_content: str) -> str:
        """
        Extract plain text from HTML content using BeautifulSoup.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove images
        for img in soup.find_all('img'):
            img.decompose()
        
        # Remove scripts and styles
        for tag in soup.find_all(['script', 'style']):
            tag.decompose()
        
        # Remove ads and promotional content
        for ad in soup.find_all(string=re.compile(r'promoted|advertisement|ad')):
            ad.decompose()
        
        # Remove line breaks and normalize whitespace
        texts = [str(t) for t in soup.find_all(string=lambda t: t and not isinstance(t, re.compile)) and not t.strip().startswith('https://')]
        return ' '.join(texts)


class GmailBookMyShowClient:
    """
    Client for interacting with Gmail API to fetch BookMyShow emails.
    Handles OAuth authentication and email retrieval.
    """
    
    def __init__(self, credentials: Credentials, project_id: str):
        """
        Initialize Gmail client with OAuth credentials.
        """
        self.credentials = credentials
        self.project_id = project_id
        self.service = None
    
    def initialize(self):
        """Initialize Gmail service if not already done."""
        if self.service is None:
            self.service = build('gmail', 'v1', credentials=self.credentials)
            print("✓ Gmail API service initialized")
    
    def get_email_query(self, max_results: int = 10) -> str:
        """
        Generate Gmail search query for BookMyShow emails.
        """
        from_email_parts = []
        for pattern in BOOKMYSHOW_EMAIL_PATTERNS:
            from_email_parts.append(f'from:{pattern}')
        
        subjects = []
        for keyword in BOOKING_SUBJECT_KEYWORDS:
            subjects.append(keyword)
        
        email_pattern = " OR ".join(from_email_parts)
        subject_pattern = " OR ".join(subjects)
        
        query = f"({email_pattern}) AND ({subject_pattern})"
        
        return query
    
    def fetch_emails(self, max_results: int = 20) -> List[Dict]:
        """
        Fetch BookMyShow emails from Gmail.
        Returns list of email metadata.
        """
        if not self.service:
            self.initialize()
        
        results = []
        query = self.get_email_query(max_results)
        
        try:
            response = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = response.get('messages', [])
            
            for msg in messages:
                email_data = {
                    'id': msg['id'],
                    'threadId': msg['threadId'],
                    'subject': msg['snippet'].get('subject', ''),
                    'from': msg['snippet'].get('from', ''),
                    'date': msg['internalDate'],
                    'raw': None,  # Will fetch raw email content on demand
                }
                
                # Fetch full email body (HTML)
                try:
                    msg_result = self.service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                    email_data['raw'] = msg_result['payload']['parts'][0]['body']['data'] if msg_result['payload']['parts'] else None
                    email_data['html'] = msg_result['payload']['parts'][0]['body'].get('html', {}).get('data') if len(msg_result['payload']['parts']) > 1 and msg_result['payload']['parts'][0].get('body').get('data') else msg_result['payload']['body'].get('html', {}).get('data')
                except IndexError:
                    email_data['raw'] = None
                    email_data['html'] = None
                    
                results.append(email_data)
                
        except HttpError as error:
            print(f"Error fetching emails: {error}")
            raise GmailAPIError(f"Failed to fetch emails: {str(error)}")
        
        return results
    
    def fetch_email_content(self, email_id: str) -> Optional[str]:
        """
        Fetch HTML content of a specific email.
        """
        try:
            msg = self.service.users().messages().get(userId='me', id=email_id, format='full').execute()
            
            # Try to get HTML part
            if 'parts' in msg['payload'] and len(msg['payload']['parts']) > 0:
                part0 = msg['payload']['parts'][0]
                if 'body' in part0 and 'data' in part0['body']:
                    # Raw text
                    raw_text = part0['body']['data']
                    
                    # Try second part for HTML
                    if len(msg['payload']['parts']) > 1:
                        part1 = msg['payload']['parts'][1]
                        if 'body' in part1 and 'html' in part1['body']:
                            return part1['body']['html']['data']
                    elif 'html' in part0.get('body', {}):
                        return part0['body']['html']['data']
                    
                    # If no HTML, return raw text
                    return raw_text
                    
            return None
            
        except HttpError as error:
            print(f"Error fetching email {email_id}: {error}")
            return None


class BookMyShowBookingParser:
    """
    Deterministic parser for BookMyShow booking confirmation emails.
    Uses regex patterns and BeautifulSoup for field extraction.
    Routes ambiguous extractions to Ollama for cleanup.
    """
    
    # Date/time pattern for Indian date format
    DATE_PATTERNS = [
        r'(?:show\s*)?(?:date|date:)?\s*[:\-]\s*(\d{1,2})/(\d{1,2})/(\d{2,4})',  # DD/MM/YYYY or D/M/YYYY
        r'(?:show\s*)?(?:date|date:)?\s*[:\-]\s*(\d{1,2})-(\d{1,2})-(\d{2,4})',  # DD-MM-YYYY
        r'(?:show\s*)?(?:date|date:)?\s*(\d{4})\s*[:\-]\s*(\d{1,2})\s*[:\-]\s*(\d{1,2})',  # YYYY:MM:DD or YYYY-MM-DD
        r'(?:time|time:)?\s*[:\-]\s*(\d{1,2})[:]\s*(\d{2})',  # HH:MM
        r'(?:time|time:)?\s*(\d{1,2})[:\-]\s*(\d{2})',
    ]
    
    # Amount pattern (₹1234.56 or INR 1234.56)
    AMOUNT_PATTERNS = [
        r'₹\s*(\d+)[\.](\d{2})',
        r'INR\s*₹?\s*(\d+)[\.](\d{2})',
        r'INR\s*\d+\.?\d*\.?\s*\(',
        r'₹\s*(\d+[,.]\d{2})',
    ]
    
    def __init__(self, ollama_client=None, tmdb_client=None):
        """
        Initialize parser with optional Ollama and TMDb clients.
        """
        self.ollama_client = ollama_client
        self.tmdb_client = tmdb_client
    
    def parse_email(self, email_data: Dict) -> BookingRecord:
        """
        Parse a single BookMyShow email and extract booking record.
        """
        record = BookingRecord()
        record.raw_email_data = email_data
        
        html_content = email_data.get('html')
        if not html_content:
            return record  # No HTML content to parse
        
        # Extract plain text from HTML
        text_content = BookMyShowEmailParser.extract_text_from_html(html_content)
        
        # Use regex to find all required fields
        self._extract_fields_from_text(text_content, record)
        
        # Check if any required field is missing
        required_fields = ['booking_id', 'event_name', 'venue', 'show_date', 'amount_paid']
        missing_fields = [f for f in required_fields if not getattr(record, f)]
        
        # If missing fields, attempt to extract from regex matches only (not from structured parsing)
        if missing_fields:
            fallback_extractor = BookMyShowFallbackExtractor()
            fallback_extractor.extract(email_data.get('raw'), record)
        
        # Calculate confidence score
        record.confidence_score = self._calculate_confidence(record)
        
        # If confidence is low, use Ollama for cleanup
        if record.confidence_score < 70 and self.ollama_client:
            record = self._enrich_with_ollama(record)
        
        # Try TMDb for poster if it's a movie and no poster URL
        if record.category == "movie" and not record.poster_url and self.tmdb_client:
            record.poster_url = self.tmdb_client.fetch_poster(record.event_name).get('poster_url')
        
        return record
    
    def _extract_fields_from_text(self, text: str, record: BookingRecord):
        """
        Extract booking fields from parsed email text using regex.
        """
        # 1. Booking ID - usually at the top of the email
        booking_id_match = re.search(r'(?:booking\s+)?id(?:|\s+#[\s:]*)(\w+[\d\-]+)', text, re.IGNORECASE | re.DOTALL)
        if booking_id_match:
            record.booking_id = booking_id_match.group(0).replace('#', '').strip()
        
        # 2. Event Name - usually prominent in the email
        # Common patterns: "Book your tickets for <Event Name>", "<Event Name> - <Venue>"
        event_patterns = [
            r'(?:book\s+)?your\s+ticket(?:s)?(?:\s+for\s+)?\s*(.+?)(?:\n|$)',
            r'(?:(?:booking\s+)?for\s+)?(?:<[^>]+>)?\s*([A-Za-z\s]+?)(?:\s*-\s*[A-Z][a-z].*?)?(?:\n|$)',
            r'(?:event|show)\s*[:\-:]\s*([A-Za-z\s]+?)\s*(?:-|on\s+\d+)',
        ]
        
        for pattern in event_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match and match.group(1).strip():
                record.event_name = match.group(1).strip()
                break
        
        # 3. Venue - usually with the event name
        venue_patterns = [
            r'([\dA-Z]+(?:\s*[A-Z]+)+)(?:[^a-zA-Z]India|[^a-zA-Z]Delhi[^a-zA-Z])',  # VENUE-India or VENUE, Delhi
            r'(?:venue|venue:)?:\s*([A-Z][A-Z\s]+[A-Z])',
            r'([A-Z][a-z][A-Z][a-z]+(?:\s+Center|Studio|Complex|Theatre|Halls?))',
        ]
        
        for pattern in venue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1).strip():
                record.venue = match.group(1).strip()
                break
        
        # 4. Show Date - DD/MM/YYYY format
        date_patterns = [
            r'(?:show\s+)?(?:date|date:)?:?\s*(\d{1,2})/(\d{1,2})/(\d{2,4})',
            r'(\d{1,2})-(\d{1,2})-(\d{2,4})(?:\s+at\s+)?',
            r'(?:date:)?:?\s*([\w\s]+?)\s+at\s+(?:([\w\s]+)?)',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1) and match.group(2):
                day, month, year = match.group(1), match.group(2), match.group(3)
                record.show_date = f"{day}/{month}/{year}"
                break
        
        # 5. Seats - seat number(s)
        seat_patterns = [
            r'(?:seat|seat\s+no|seat#)?:?\s*(\d+)',
            r'(?:seats?:?)?\s+(\d+)',
            r'Block\s+([A-Z]+)-[\s]*(\d+)',
            r'(\w{2})(\d+)',  # BlockAA-123
        ]
        
        for pattern in seat_patterns:
            match = re.search(pattern, text)
            if match and match.group(0).isdigit():
                record.seats = match.group(0)
                break
        
        # 6. Amount - total amount paid
        amount_patterns = [
            r'₹\s*(\d+)[\.](\d{2})',
            r'INR\s*₹\s*(\d+)',
            r'Total\s*(?:amount|payable|paid):?\s*₹\s*(\d+)[\.](\d{2})',
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1) and match.group(2):
                record.amount_paid = float(f"{match.group(1)}.{match.group(2)}")
                break
        
        # 7. Category - infer from event name or explicit mention
        # Explicit category mentions
        category_keywords = {
            'movie': ['movie', 'film', 'cinema', 'theatrical'],
            'concert': ['concert', 'live concert', 'live event'],
            'sports': ['sports', 'match', 'game', 'fixture', 'cricket', 'football', 'hockey'],
            'comedy': ['comedy', 'stand-up', 'stand up', 'comedian'],
            'play': ['play', 'theatre', 'musical'],
        }
        
        event_text = record.event_name or ''
        for cat, keywords in category_keywords.items():
            for kw in keywords:
                if kw.lower() in event_text.lower():
                    record.category = cat
                    break
            if record.category:
                break
        
        if not record.category:
            record.category = "uncategorized"
        
        # Default show_time if not found
        if not record.show_time:
            record.show_time = "TBD"
    
    def _calculate_confidence(self, record: BookingRecord) -> float:
        """
        Calculate confidence score (0-100) for the extraction.
        Based on presence and quality of extracted fields.
        """
        scores = []
        
        # Required fields - heavy weight
        if record.booking_id:
            scores.append((100, record.booking_id.replace('#', '').isdigit() or len(record.booking_id) >= 4))
        if record.event_name:
            scores.append((100, len(record.event_name) >= 3))
        if record.venue:
            scores.append((100, len(record.venue) >= 3))
        if record.show_date:
            scores.append((80, self._validate_date(record.show_date) == record.show_date))
        if record.amount_paid:
            scores.append((90, record.amount_paid > 0))
        
        # Optional fields - lighter weight
        if record.seats:
            scores.append((70, record.seats.isdigit() or len(record.seats) <= 10))
        if record.poster_url:
            scores.append((50, record.poster_url.startswith('http')))
        
        # Calculate weighted average
        if scores:
            total_score = sum(score[0] * (1 if score[1] else 0) for score in scores)
            return total_score / sum(score[0] for score in scores)
        
        return 0.0
    
    def _validate_date(self, date_str: str) -> bool:
        """Validate if date string is in DD/MM/YYYY or MM/DD/YYYY format."""
        parts = date_str.split('/')
        if len(parts) != 3:
            return False
        
        day, month, year = parts
        # Days: 01-31, Months: 01-12, Year: 2020-2099
        return 1 <= int(day) <= 31 and 1 <= int(month) <= 12 and 2020 <= int(year) <= 2099
    
    def _enrich_with_ollama(self, record: BookingRecord) -> BookingRecord:
        """
        Use Ollama to clean up low-confidence extractions.
        """
        enrichment_needed = False
        enriched_record = BookingRecord()
        enriched_record.raw_email_data = record.raw_email_data
        enriched_record.confidence_score = record.confidence_score
        
        # Enrich venue name if present but low confidence or has known issues
        if record.venue and record.confidence_score >= 50:
            # Remove common suffixes
            cleaned_venue = self._clean_venue_name(record.venue)
            if cleaned_venue != record.venue:
                enriched_record.venue = cleaned_venue
                enrichment_needed = True
            else:
                enriched_record.venue = record.venue
        
        # Infer category if not clearly determined
        if record.category == "uncategorized" and record.confidence_score >= 50:
            result = self.ollama_client.infer_category(record.event_name)
            if result.get('confidence_score', 0) > 0.6 and result.get('category'):
                enriched_record.category = result['category']
                enrichment_needed = True
        
        # Generate blurb if Ollama available
        if self.ollama_client:
            result = self.ollama_client.generate_blurb(
                record.event_name, 
                record.show_date or "TBD",
                record.venue
            )
            if result.get('blurb') and result.get('confidence_score', 0) > 0.6:
                enriched_record.blurb = result['blurb']
                enrichment_needed = True
        
        return enriched_record
    
    def _clean_venue_name(self, venue: str) -> str:
        """
        Clean venue name by removing common artifacts.
        """
        # Remove Indian location suffix
        venue = re.sub(r'\s*India$', '', venue, flags=re.IGNORECASE)
        venue = re.sub(r',\s*India$', '', venue)
        venue = re.sub(r'\s*Delhi$', '', venue, flags=re.IGNORECASE)
        venue = re.sub(r',\s*Delhi$', '', venue)
        venue = re.sub(r'\s*Mumbai$', '', venue, flags=re.IGNORECASE)
        venue = re.sub(r',\s*Mumbai$', '', venue)
        venue = re.sub(r'\s*Bangalore$', '', venue, flags=re.IGNORECASE)
        venue = re.sub(r',\s*Bangalore$', '', venue)
        venue = re.sub(r'\s*Kolkata$', '', venue, flags=re.IGNORECASE)
        venue = re.sub(r',\s*Kolkata$', '', venue)
        
        # Remove common phrases
        venue = re.sub(r'\s*at\s', '', venue)
        venue = re.sub(r'\s*in\s', '', venue)
        venue = re.sub(r'\s*The\s', '', venue, flags=re.IGNORECASE)
        venue = re.sub(r'\s*A\s', '', venue, flags=re.IGNORECASE)
        venue = re.sub(r'\s*An\s', '', venue, flags=re.IGNORECASE)
        
        # Remove duplicates and extra spaces
        venue = re.sub(r'\s+', ' ', venue)
        venue = venue.strip()
        
        return venue


class BookMyShowFallbackExtractor:
    """
    Fallback extractor that tries to parse raw email data when structured parsing fails.
    Used when no HTML is available or structured extraction finds missing required fields.
    """
    
    @staticmethod
    def extract(raw_email: str, record: BookingRecord):
        """
        Extract booking record from raw HTML email content.
        """
        if not raw_email:
            return
        
        # Try to find email in raw content
        raw_soup = BeautifulSoup(raw_email, 'html.parser')
        
        # Look for common patterns in the raw HTML
        raw_text = ''
        for element in raw_soup.find_all(['div', 'p', 'span']):
            raw_text += element.get_text() + ' '
        
        # Try basic regex on raw text
        # Booking ID
        booking_id_match = re.search(r'(?:booking\s+)?id[\s:]*([A-Za-z0-9\-]+)', raw_text, re.IGNORECASE)
        if booking_id_match:
            record.booking_id = booking_id_match.group(1)
        
        # Event name - simpler pattern
        event_match = re.search(r'(?:[<>][A-Za-z\s]+[<>])\s+[\-:]\s*([A-Za-z\s]+?)(?:[\n]|$)', raw_text, re.IGNORECASE)
        if event_match:
            record.event_name = event_match.group(1).strip()
        elif event_match:
            record.event_name = record.event_name or event_match.group(1).strip()
        
        # Venue
        venue_match = re.search(r'(?:venue|venue:)[:\s]*([A-Z][A-Z\s]+[A-Z])', raw_text, re.IGNORECASE)
        if venue_match:
            record.venue = venue_match.group(1).strip()
        
        # Date
        date_match = re.search(r'(?:show\s+)?(?:date|:)?:?\s*(\d{1,2})/(\d{1,2})/(\d{2,4})', raw_text, re.IGNORECASE)
        if date_match:
            day, month, year = date_match.groups()
            record.show_date = f"{day}/{month}/{year}"
        
        # Seats
        seat_match = re.search(r'(?:seat|seats)[:\s]*(\d+)', raw_text)
        if seat_match and seat_match.group(1).isdigit():
            record.seats = seat_match.group(1)
        
        # Amount
        amount_match = re.search(r'₹\s*(\d+)[\.](\d{2})', raw_text)
        if amount_match:
            record.amount_paid = float(f"{amount_match.group(1)}.{amount_match.group(2)}")


async def main():
    """
    Test the email fetching and parsing pipeline.
    """
    print("\n=== Testing BookMyShow Email Pipeline ===\n")
    
    # Simulate credentials (in real use, call setup_gmail_oauth.py first)
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    
    creds = Credentials(min_token_expiry=0)
    
    client = GmailBookMyShowClient(creds, "test-project")
    
    # Fetch emails
    emails = client.fetch_emails(max_results=5)
    print(f"✓ Found {len(emails)} BookMyShow emails")
    
    # Parse each email
    for email in emails:
        record = BookMyShowBookingParser().parse_email(email)
        print(f"\n--- Email ID: {email['id']} ---")
        print(f"  Subject: {email['subject']}")
        print(f"  From: {email['from']}")
        print(f"  Booking ID: {record.booking_id}")
        print(f"  Event: {record.event_name}")
        print(f"  Venue: {record.venue}")
        print(f"  Date: {record.show_date}")
        print(f"  Time: {record.show_time}")
        print(f"  Seats: {record.seats}")
        print(f"  Amount: ₹{record.amount_paid}")
        print(f"  Category: {record.category}")
        print(f"  Confidence: {record.confidence_score:.0f}%")
        print(f"  Poster: {record.poster_url}")
        
        if record.confidence_score < 70:
            print(f"  ⚠️  Low confidence - would route to Ollama for cleanup")
        else:
            print(f"  ✓ High confidence - deterministic extraction")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())