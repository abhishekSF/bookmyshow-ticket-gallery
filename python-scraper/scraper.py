"""
BookMyShow Email Scraper with Ollama Enrichment

This script:
1. Connects to Gmail API to fetch BookMyShow booking confirmation emails
2. Parses emails deterministically using BeautifulSoup + regex
3. Uses Ollama (local LLM) for text cleanup/enrichment only
4. Fetches poster art via TMDb API for movies
5. Outputs structured tickets.json

Author: Sunday Project - BookMyShow Ticket Gallery + Salesforce Headless 360
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
import google.auth
import google.auth.transport.requests
import googleapiclient.discovery
from googleapiclient.errors import HttpError

# Try to import TMDb for poster fallback
try:
    import requests
    TMDB_API_KEY = os.environ.get('TMDB_API_KEY', '')
    if not TMDB_API_KEY:
        print("Warning: TMDB_API_KEY not set. Poster fallback will use placeholders.")
    tmdb_headers = {"Authorization": "Bearer " + TMDB_API_KEY} if TMDB_API_KEY else {}
except ImportError:
    requests = None
    TMDB_API_KEY = ""
    tmdb_headers = {}

# --- Configuration ---
GMAIL_QUERY = 'from:noreply@bookmyshow.com OR from:bookmyshow'
# Also support alternative sender addresses
GMAIL_QUERY_ALT = 'from:bookmyshow.com OR subject:Booking Confirmation OR subject:confirmed ticket'
MAX_PAGES = 5  # Limit Gmail search pages to avoid rate limits
LLM_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')
LLM_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')

# Ollama enrichment: only add if confidence is low or field is missing
ENRICHMENT_ENABLED = os.environ.get('ENRICHMENT_ENABLED', 'true').lower() == 'true'
TMDB_FALLBACK = os.environ.get('TMDB_FALLBACK', 'true').lower() == 'true'

# --- Gmail API Helper ---

def get_gmail_service():
    """Initialize Gmail API service with OAuth2 credentials."""
    creds = None
    token_path = os.path.expanduser('~/google_drive_oauth/token.json')
    
    if os.path.exists(token_path):
        creds = google.auth.load_user_credentials(token_path)
    
    # Also check in project root for dev use
    local_token = os.path.join(os.path.dirname(__file__), 'token.json')
    if os.path.exists(local_token):
        creds = google.auth.load_user_credentials(local_token)
    
    request = google.auth.transport.requests.Request()
    
    service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)
    
    return service, token_path

def search_emails(service, query, max_results=100):
    """Search Gmail for emails matching the query."""
    results = []
    pages = min(max_results, MAX_PAGES)
    
    for _ in range(pages):
        try:
            results = service.users_messages().list(
                userId='me',
                q=query,
                maxResults=10,
                pageToken=service._client.get_token()  # Will handle pagination
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                break
                
            for msg in messages:
                msg_data = msg['payload']['headers']
                body = msg['payload']['body']
                parts = body.get('data', [])
                if parts:
                    body_data = ','.join(p.get('data', '') for p in parts)
                    body_content = f"{body_data}\n{body.get('snippet', '')}"
                else:
                    body_content = body.get('snippet', '')
                
                results.append({
                    'id': msg['id'],
                    'threadId': msg['threadId'],
                    'from': msg_data[0]['value'] if msg_data else '',
                    'subject': msg_data[-1]['value'] if msg_data else '',
                    'body': body_content,
                    'html': body_content if 'html' in body else ''
                })
                
                if len(results) >= max_results:
                    break
                    
        except HttpError as e:
            if e.resp['code'] == 403:
                print(f"Gmail rate limit or permission issue. Retry in 30s.")
                time.sleep(30)
            else:
                raise
            continue
            
        time.sleep(1)  # Be respectful of Gmail rate limits
        
    return results

# --- Email Parsing Logic ---

def parse_bookmyshow_email(email_data) -> Optional[dict]:
    """
    Deterministically parse BookMyShow email using BeautifulSoup + regex.
    Returns structured ticket record or None if parsing fails.
    
    Handles multiple email templates (movies, events, sports, etc.)
    """
    raw_html = email_data.get('html', '')
    raw_text = email_data.get('body', '')
    subject = email_data.get('subject', '')
    sender = email_data.get('from', '')
    
    # Clean HTML tags from body for fallback text parsing
    clean_body = BeautifulSoup(raw_html, 'html.parser').get_text()
    
    ticket = {
        'booking_id': None,
        'event_name': None,
        'event_title': None,  # Short title for lookups
        'venue': None,
        'show_date': None,
        'show_time': None,
        'start_time': None,
        'end_time': None,
        'venue_address': None,
        'city': None,
        'seats': None,
        'amount_paid': None,
        'currency': 'INR',
        'poster_url': None,
        'category': None,  # movie, concert, sports, comedy, etc.
        'confidence': 100,
        'parsing_issues': [],
        'raw_email_id': email_data.get('id'),
    }
    
    confidence = 100
    issues = []
    
    # --- Extract Booking ID ---
    # Common patterns in BMS emails
    booking_patterns = [
        r'Booking\s*(?:ID|Number|Reference)[:\s]*([A-Z0-9]{6,12})',
        r'Booking Reference[:\s]*([A-Z0-9]{6,12})',
        r'bookingId[:\s]*([A-Z0-9]{6,12})',
        r'ID[:\s]*([A-Z0-9]{6,12})',
        r'(#\d{4,})',  # Fallback to just a number
    ]
    
    matched_booking_id = None
    for pattern in booking_patterns:
        match = re.search(pattern, clean_body, re.IGNORECASE)
        if match:
            candidate = match.group(1).upper()
            if len(candidate) >= 6 and re.match(r'^[A-Z0-9]{6,12}$', candidate):
                matched_booking_id = candidate
                break
    
    if matched_booking_id:
        ticket['booking_id'] = matched_booking_id
    else:
        issues.append("booking_id not found in email")
        confidence -= 20
    
    # --- Extract Event Name / Title ---
    # Look for "Event:", "For your booking:", "movie name", "show name"
    event_patterns = [
        r'(?:For\s+your\s+booking|Event|Movie|Show|Concert|Match):\s*([^\n]+?)(?:\n|$)',
        r'(?:\n\s*)?([A-Z][^\n@]+?)(?:\n|\n\s*(?:Venue|Date|Seats|amount))',
        r'"([A-Z][A-Z\s\-()\'\'\s]+\d{1,4})"',  # HTML data attribute pattern
    ]
    
    matched_event = None
    for pattern in event_patterns:
        match = re.search(pattern, clean_body, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Filter out header text
            if len(candidate) > 3 and not any(x in candidate.lower() for x in ['booking confirmation', 'terms', 'condition', 'receipt']):
                matched_event = candidate
                break
    
    if matched_event:
        ticket['event_name'] = matched_event
        ticket['event_title'] = matched_event[:40] if len(matched_event) > 40 else matched_event
    else:
        issues.append("event name not clearly identified")
        confidence -= 25
    
    # --- Extract Date / Time ---
    # Look for date patterns: "Sat, 12 Aug 2025", "12 Aug 2025", "August 12, 2025", etc.
    date_patterns = [
        r'(?:Sat|Sun|Mon|Tue|Wed|Thu|Fri),\s*(\d{1,2})\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})',
        r'(?:\d{1,2})\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})',
        r'(\d{1,2})\s*(?:August|Aug)\s*(\d{4})',  # Specific to Indian context
        r'(?:\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
        r'(\d{4})-(\d{1,2})',  # YYYY-MM
    ]
    
    matched_date = None
    matched_month = None
    
    for pattern in date_patterns:
        match = re.search(pattern, clean_body, re.IGNORECASE)
        if match:
            candidates = match.groups()
            for i, c in enumerate(candidates):
                if c and re.match(r'^\d+$', c):
                    matched_date = c
                    matched_month = pattern[i].upper()[:3] if pattern[i] else None
                    break
            if matched_date:
                break
    
    if matched_date:
        ticket['show_date'] = matched_date
        if matched_month:
            ticket['show_date'] = f"{matched_date} {matched_month} 2025" if matched_date in ['1', '2', '3', '4', '5', '6', '7', '8'] else f"{matched_date} {matched_month} 2026"
    else:
        issues.append("show date not found")
        confidence -= 30
    
    # --- Extract Time ---
    time_patterns = [
        r'(?:Show|Start)[:\s]*(\d{1,2}:\d{2}[AP]\.?\d{2}?)',
        r'Time[:\s]*(\d{1,2}:\d{2}[AP]\.?\d{2}?)',
        r'(?:\d{1,2}:\d{2})\s*(?:PM|AM)',
    ]
    
    matched_time = None
    for pattern in time_patterns:
        match = re.search(pattern, clean_body, re.IGNORECASE)
        if match:
            candidate = match.group(1)
            if candidate and ':' in str(candidate) and len(candidate) <= 10:
                matched_time = str(candidate)
                break
    
    if matched_time:
        ticket['show_time'] = matched_time
    else:
        issues.append("show time not found")
        confidence -= 15
    
    # --- Extract Venue ---
    # Look for venue patterns
    venue_patterns = [
        r'Venue[:\s]*([^\n@]+?)(?:\n|$)',
        r'Location[:\s]*([^\n@]+?)(?:\n|$)',
        r'Theatre[:\s]*([^\n@]+?)(?:\n|$)',
    ]
    
    matched_venue = None
    for pattern in venue_patterns:
        match = re.search(pattern, clean_body, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if len(candidate) > 2 and not any(x in candidate.lower() for x in ['pune', 'mumbai', 'delhi', 'city']):  # Filter out generic terms
                # Also filter if it's not a specific theater
                if not re.search(r'(?:Metro|Cinema|Mall|Express)[:\s]+$', candidate, re.IGNORECASE):
                    matched_venue = candidate
                    break
    
    if matched_venue:
        ticket['venue'] = matched_venue
    else:
        # Try to extract from "Venue Address" pattern
        address_match = re.search(r'Address[:\s]*([^\n@]+?)(?:\n|$)', clean_body)
        if address_match:
            venue_address = address_match.group(1).strip()
            # Extract venue name from address
            parts = venue_address.split(',')
            if parts:
                ticket['venue'] = parts[0] if parts[0] not in ['India', 'Pune', 'Mumbai', 'Delhi'] else parts[-2]
                ticket['city'] = parts[-1] if len(parts) > 1 else None
    
    if not ticket['venue']:
        issues.append("venue not clearly identified")
        confidence -= 20
    
    # --- Extract Seats ---
    # Look for "Seats:", "Seat Numbers:", etc.
    seat_patterns = [
        r'Seats[:\s]*(\d+(?:\s*(?:to\s*\d+)?)?)',
        r'Seat\s+Numbers[:\s]*([^\n]+?)(?:\n|$)',
        r'Row\s*([A-Z])?\s*-\s*Seat\s*([A-Z]\d+)',
        r'Seat(?:s)?[:\s]*(\d+)',
    ]
    
    matched_seats = None
    for pattern in seat_patterns:
        match = re.search(pattern, clean_body, re.IGNORECASE)
        if match:
            candidate = match.group(1)
            if candidate:
                # Extract just the numbers
                numbers = re.findall(r'\d+', candidate)
                if numbers:
                    if len(numbers) == 2:
                        matched_seats = f"{numbers[0]}-{numbers[1]}"
                    elif len(numbers) == 1:
                        matched_seats = numbers[0]
                    else:
                        matched_seats = ','.join(numbers)
                break
    
    if matched_seats:
        ticket['seats'] = matched_seats
    else:
        issues.append("seats not found")
        confidence -= 25
    
    # --- Extract Amount ---
    # Look for amount patterns with INR currency
    amount_patterns = [
        r'₹\s*(\d{3,6}(?:\.\d{2})?)',
        r'Rs\.?\s*₹\s*(\d{3,6}(?:\.\d{2})?)',
        r'Amount[:\s]*₹\s*(\d{3,6}(?:\.\d{2})?)',
        r'Payment Amount[:\s]*₹\s*(\d{3,6}(?:\.\d{2})?)',
        r'Total Amount[:\s]*₹\s*(\d{3,6}(?:\.\d{2})?)',
        r'INR\s*(\d{3,6}(?:\.\d{2})?)',
    ]
    
    matched_amount = None
    matched_currency = 'INR'
    
    for pattern in amount_patterns:
        match = re.search(pattern, clean_body, re.IGNORECASE)
        if match:
            candidate = match.group(1)
            if re.match(r'^\d+', candidate):
                matched_amount = candidate
                break
    
    if matched_amount:
        ticket['amount_paid'] = matched_amount
    else:
        # Try alternate currency formats
        amount_alt = re.search(r'₹?\s*Rs?\.(?\d{3,6}(?:\.\d{2})?)', clean_body)
        if amount_alt:
            ticket['amount_paid'] = amount_alt.group(1).replace('.', '')
            if ticket['amount_paid'] and len(ticket['amount_paid']) > 5:
                ticket['currency'] = 'INR'
        else:
            issues.append("amount not found")
            confidence -= 15
    
    # --- Extract Poster URL ---
    # Look for image URLs in the HTML
    poster_patterns = [
        r'data-url["\']?[:\s]*["\']?(https?://[^\s"\']+)["\']?',
        r'poster["\']?[:\s]*["\']?(https?://[^\s"\']+)["\']?',
        r'img-src["\']?[:\s]*["\']?(https?://[^\s"\']+)["\']?',
        r'background-image["\']?[:\s]*["\']?(https?://[^\s"\']+)["\']?',
    ]
    
    matched_poster = None
    for pattern in poster_patterns:
        match = re.search(pattern, raw_html)
        if match:
            candidate = match.group(1)
            if candidate and ('movie' in candidate.lower() or 'poster' in candidate.lower()):
                matched_poster = candidate
                break
    
    if matched_poster and (matched_poster.startswith('http://') or matched_poster.startswith('https://')):
        ticket['poster_url'] = matched_poster
    else:
        issues.append("poster URL not found in email")
        confidence -= 15
    
    # Check overall confidence
    if confidence < 50:
        return None  # Too low confidence, skip this email
    
    return ticket


def enrich_with_ollama(ticket: dict, ollama_client):
    """
    Use Ollama to clean up and enrich ticket data.
    Only modifies fields with low confidence or missing values.
    
    Returns updated ticket dict.
    """
    if not ENRICHMENT_ENABLED or not ollama_client:
        return ticket
    
    updates = {
        'venue': ticket.get('venue'),
        'category': ticket.get('category'),
        'blurb': '',
    }
    
    system_prompt = f"""You are a data cleanup assistant for BookMyShow booking confirmations.
Your task is to clean up and enhance the following ticket record.
DO NOT change or generate: booking_id, show_date, amount_paid.
Only modify venue (correct spelling/inconsistencies) and add category/inferred genre.
Add a ONE-SENTENCE blurb about the event.
Return ONLY valid JSON, no markdown formatting.

Ticket data to clean:
{json.dumps(ticket, indent=2)}

Respond with JSON keys:
- venue: Cleaned venue name
- category: Inferred genre (movie/concert/sports/comedy/play/theatre)
- blurb: One sentence description
"""
    
    try:
        response = ollama_client.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Ticket data:\n{json.dumps(ticket, indent=2)}"},
            ],
        )
        
        # Extract JSON from response
        json_str = response['message']['content']
        
        # Try to parse the JSON
        try:
            enriched = json.loads(json_str)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            match = re.search(r'```(?:json)?\s*(.*?)```', json_str, re.DOTALL)
            if match:
                json_str = match.group(1)
                enriched = json.loads(json_str.strip())
            else:
                # Fallback: return original
                return ticket
        
        # Merge updates
        for key, value in enriched.items():
            if key == 'venue':
                if ticket['venue']:
                    ticket['venue'] = value.strip() + " " + ticket['venue'].strip()
                    ticket['venue'] = ticket['venue'].split(',')[-1]  # Keep the specific venue
                else:
                    ticket['venue'] = value.strip()
            elif key == 'category':
                if not ticket.get('category'):
                    ticket['category'] = value.strip()
            elif key == 'blurb':
                ticket['blurb'] = value.strip()
                
    except Exception as e:
        print(f"Ollama enrichment failed: {e}. Skipping.")
    
    return ticket


def get_tmdb_poster(title: str) -> Optional[str]:
    """
    Fetch poster URL from TMDb API for the given movie title.
    Returns poster URL or None if not found.
    """
    if not requests or not TMDB_API_KEY:
        return None
    
    query = f"movie,original_title={title.replace(' ', '+')}"
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={title.replace(' ', '+')}"
    
    try:
        resp = requests.get(url, headers=tmdb_headers, timeout=10)
        data = resp.json()
        
        # Look for exact match
        for movie in data.get('results', [])[:10]:  # Check top 10 results
            if movie.get('original_title', '').lower() == title.lower():
                return f"https://image.tmdb.org/t/p/w500{movie.get('posters', [''])[0]}"
            elif movie.get('title', '').lower() == title.lower():
                return f"https://image.tmdb.org/t/p/w500{movie.get('poster_path', '')}"
        
        # If no exact match, return highest scoring
        if data.get('results'):
            return f"https://image.tmdb.org/t/p/w500{data['results'][0].get('posters', [''])[0]}"
            
    except Exception as e:
        print(f"TMDb lookup failed: {e}")
    
    return None


def categorize_event(title: str) -> str:
    """
    Infer category from event title using keyword matching.
    """
    title_lower = title.lower()
    
    # Movie keywords
    if any(k in title_lower for k in ['movie', 'film', 'cinema', 'cinemas', 'theater']):
        return 'movie'
    
    # Concert keywords
    if any(k in title_lower for k in ['concert', 'live', 'live concert', 'tour']):
        return 'concert'
    
    # Sports keywords
    if any(k in title_lower for k in ['match', 'game', 'cricket', 'football', 'tennis', 'basketball', 'hockey']):
        return 'sports'
    
    # Comedy keywords
    if any(k in title_lower for k in ['comedy', 'standup', 'funny', 'laughter']):
        return 'comedy'
    
    # Play/Theatre keywords
    if any(k in title_lower for k in ['play', 'theatre', 'musical', 'drama', 'theatrical']):
        return 'play'
    
    # Default
    return 'uncategorized'


# --- Main Scraper ---

def main():
    """
    Main entry point for the BookMyShow email scraper.
    """
    print("🎟️  BookMyShow Ticket Scraper v1.0")
    print("=" * 50)
    
    service, token_path = get_gmail_service()
    
    print("✓ Gmail API connected")
    print(f"  Credentials: {token_path}")
    
    # Search for BookMyShow emails
    emails = search_emails(service, GMAIL_QUERY)
    
    if not emails:
        print("✗ No BookMyShow emails found.")
        sys.exit(1)
    
    print(f"\n📧 Found {len(emails)} BookMyShow email(s)")
    
    tickets = []
    
    for email in emails:
        print(f"\nProcessing: {email['id']}")
        print(f"  Subject: {email['subject']}")
        print(f"  Sender: {email['from']}")
        
        ticket = parse_bookmyshow_email(email)
        
        if ticket:
            # Categorize if not already set
            if not ticket['category']:
                ticket['category'] = categorize_event(ticket['event_name'] or ticket['event_title'])
            
            # Fetch poster if missing
            if not ticket['poster_url'] and ticket['event_name']:
                if TMDB_FALLBACK:
                    poster = get_tmdb_poster(ticket['event_name'])
                    if poster:
                        ticket['poster_url'] = poster
                else:
                    # Use generic placeholder based on category
                    placeholders = {
                        'movie': 'https://images.unsplash.com/photo-1489599849907-40a954b58b2c?w=500&auto=format&fit=crop&q=60',
                        'concert': 'https://images.unsplash.com/photo-1459652420828-48c7759554df?w=500&auto=format&fit=crop&q=60',
                        'sports': 'https://images.unsplash.com/photo-1504296135436-302d4a53188c?w=500&auto=format&fit=crop&q=60',
                        'comedy': 'https://images.unsplash.com/photo-1585866688066-99fc4771b039?w=500&auto=format&fit=crop&q=60',
                        'play': 'https://images.unsplash.com/photo-1507679184260-f3db19f65e20?w=500&auto=format&fit=crop&q=60',
                        'uncategorized': 'https://images.unsplash.com/photo-1543589855-f3a054b60e8c?w=500&auto=format&fit=crop&q=60',
                    }
                    ticket['poster_url'] = placeholders.get(ticket['category'], placeholders['uncategorized'])
            
            # Enrich with Ollama if low confidence
            if ticket['confidence'] < 80 and ENRICHMENT_ENABLED:
                print("  ⏳ Running Ollama enrichment...")
                ticket = enrich_with_ollama(ticket, ollama_client)
            
            tickets.append(ticket)
            print(f"  ✓ Parsed: {ticket['event_name']} at {ticket['venue']}")
            print(f"    Date: {ticket['show_date']}, Seats: {ticket['seats']}, Amount: ₹{ticket['amount_paid']}")
        else:
            print("  ✗ Could not parse this email")
    
    # Save tickets to JSON
    output_file = os.path.join(os.path.dirname(__file__), 'tickets.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tickets, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 50}")
    print(f"🎉 Saved {len(tickets)} ticket(s) to {output_file}")
    
    return tickets


if __name__ == '__main__':
    import re
    main()

"""
USAGE:
1. Set up Gmail OAuth (first run opens browser)
2. Run: python scraper.py
3. Check tickets.json for parsed results
4. Next: Configure Ollama model and run with enrichment
"""