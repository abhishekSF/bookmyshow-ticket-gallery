"""
Main scraper for BookMyShow ticket gallery.
Fetches emails from Gmail, parses them, enriches with Ollama, 
looks up posters from TMDb, and outputs structured tickets.json
"""

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from config import settings
from ollama_client import OllamaClient, PosterClient
from gmail_client import (
    GmailBookMyShowClient,
    BookMyShowBookingParser,
    BookingRecord
)
from bs4 import BeautifulSoup


def save_tickets(tickets: List[Dict], output_file: str = "tickets.json"):
    """Save parsed tickets to JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tickets, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved {len(tickets)} tickets to {output_file}")


async def fetch_tickets():
    """
    Main orchestration function:
    1. Fetch emails from Gmail
    2. Parse emails with deterministic parser
    3. Route low-confidence extractions to Ollama
    4. Fetch poster art from TMDb
    5. Save to tickets.json
    """
    
    # Initialize services
    ollama_client = OllamaClient(
        url=settings.ollama_url,
        model=settings.ollama_model,
        timeout_ms=settings.ollama_timeout_ms
    )
    
    tmdb_client = PosterClient(api_key=settings.tmdb_api_key)
    
    # Check if Ollama is available
    if settings.ollama_enable and not ollama_client.connect():
        print("⚠️  Warning: Ollama is enabled but not running. Enrichment will be skipped.")
        settings.ollama_enable = False
    
    # Initialize Gmail client
    if not settings.gmail_enabled:
        print("⚠️  Gmail is not enabled. Use 'python setup_gmail_oauth.py' first.")
        return []
    
    print("\n" + "="*60)
    print("📧 Fetching BookMyShow emails from Gmail...")
    print("="*60 + "\n")
    
    try:
        creds = _get_gmail_credentials()
        gmail_client = GmailBookMyShowClient(creds, settings.gmail_project_id)
        gmail_client.initialize()
        
        emails = gmail_client.fetch_emails(max_results=50)
        print(f"✓ Found {len(emails)} potential BookMyShow emails")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure you've run 'python setup_gmail_oauth.py' and granted permissions.")
        return []
    
    # Parse all emails
    print("\n🔍 Parsing emails with deterministic parser...")
    
    parser = BookMyShowBookingParser(
        ollama_client=ollama_client if settings.ollama_enable else None,
        tmdb_client=tmdb_client if settings.tmdb_enable else None
    )
    
    tickets = []
    low_confidence_count = 0
    
    for email in emails:
        record = parser.parse_email(email)
        
        # Only include records with some required data
        if record.event_name or record.booking_id:
            tickets.append({
                "booking_id": record.booking_id,
                "event_name": record.event_name,
                "venue": record.venue,
                "show_date": record.show_date,
                "show_time": record.show_time,
                "seats": record.seats,
                "amount_paid": record.amount_paid,
                "poster_url": record.poster_url,
                "category": record.category,
                "confidence_score": record.confidence_score,
                "parsing_notes": f"Confidence: {record.confidence_score:.0f}%",
                "extracted_at": datetime.now().isoformat(),
                "raw_subject": email.get('subject', '')[:100],
            })
            
            if record.confidence_score < 70:
                low_confidence_count += 1
    
    print(f"✓ Parsed {len(tickets)} tickets")
    if low_confidence_count > 0:
        print(f"  ⚠️  {low_confidence_count} tickets have low confidence scores")
    
    # Save to file
    save_tickets(tickets)
    
    return tickets


async def fetch_and_save_tickets():
    """Main entry point - fetch, parse, and save tickets."""
    
    print("\n" + "="*60)
    print("🎟️  BOOKMYSHOW TICKET GALLERY - SCRAPER")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Gmail enabled: {settings.gmail_enabled}")
    print(f"  Ollama enabled: {settings.ollama_enable} (model: {settings.ollama_model})")
    print(f"  TMDb enabled: {settings.tmdb_enable}")
    settings.print_status()
    
    if not settings.is_ready:
        print("\n⚠️  Some services are not ready. Continuing anyway...")
    
    tickets = await fetch_tickets()
    
    if tickets:
        print(f"\n{'='*60}")
        print("📊 Summary:")
        print(f"{'='*60}")
        
        categories = {}
        for ticket in tickets:
            cat = ticket.get('category', 'uncategorized')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\nBy Category:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")
        
        total_amount = sum(t.get('amount_paid', 0) for t in tickets if t.get('amount_paid'))
        print(f"\nTotal Amount: ₹{total_amount:,.2f}")
        
        print("\n✓ All done! Check tickets.json for the full dataset")


def _get_gmail_credentials():
    """
    Get OAuth credentials from token file or create new one.
    """
    import os
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    
    token_file = settings.gmail_token_file
    
    # Check if token file exists and is valid
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                data = json.load(f)
                token = Credentials(**{
                    'token_type': data['token_type'],
                    'access_token': data['access_token'],
                    'refresh_token': data.get('refresh_token'),
                    'expiry': data.get('expiry'),
                    'expires_in': data.get('expires_in'),
                })
                if token.valid or token.expired or token.has_refreshed():
                    return token
        except:
            pass
    
    # Create new flow
    credentials_dir = "tokens"
    os.makedirs(credentials_dir, exist_ok=True)
    
    flow = Flow.from_client_config(
        settings.gmail_client_id,
        settings.gmail_client_secret,
        scopes=SCOPES,
        cred=None,
    )
    
    flow.run_to_complete()
    
    creds = flow.credentials
    
    # Save token
    token_data = {
        'access_token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_type': creds.token_type,
        'expires_in': creds.expiry.total_seconds() if creds.expiry else 0,
    }
    
    with open(token_file, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    return creds


def main():
    """CLI entry point."""
    import click
    
    @click.command()
    @click.option('--force', is_flag=True, help='Force save even if no tickets')
    def cli(force=False):
        """Main scraper CLI."""
        asyncio.run(fetch_and_save_tickets())
    
    if __name__ == '__main__':
        cli()


if __name__ == "__main__":
    import asyncio
    asyncio.run(fetch_and_save_tickets())