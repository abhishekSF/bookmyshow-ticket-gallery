"""
Shared utilities for the BookMyShow Ticket Gallery project.
Used by Python scraper, React app, and other components.
"""

import re
from typing import Optional, List, Dict, Tuple
from datetime import datetime


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace, newlines, and non-printable chars.
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters except spaces
    text = re.sub(r'[^\w\s@._#-]', '', text)
    
    return text.strip()


def normalize_venue_name(venue: str) -> Tuple[str, bool]:
    """
    Normalize venue name by removing common suffixes.
    Returns (normalized_name, is_changed).
    
    Common suffixes to remove:
    - India, Delhi, Mumbai, Bangalore, etc. (location)
    - Deluxe, Premium, Grand (class)
    - at/in/The/A/An (prepositions)
    """
    if not venue:
        return venue, False
    
    # Remove location suffixes
    location_suffixes = [
        ' India', ' Delhi', ' Mumbai', ' Bangalore', ' Kolkata', 
        ' Chennai', ' Hyderabad', ' Pune', ' Jaipur', ' Ahmedabad'
    ]
    for suffix in location_suffixes:
        venue = venue.rstrip(suffix).rstrip()
    
    # Remove class suffixes
    class_suffixes = [
        ' Deluxe', ' Premium', ' Grand', ' Super', ' International', ' National'
    ]
    for suffix in class_suffixes:
        venue = venue.rstrip(suffix).rstrip()
    
    # Remove common prepositions at start
    prepositions = ['at ', 'At ', 'in ', 'In ', 'The ', 'the ', 'a ', 'A ', 'an ', 'An ']
    for prep in prepositions:
        if venue.startswith(prep):
            venue = venue[len(prep):]
    
    # Remove trailing hyphens
    venue = venue.rstrip('-,;:.')
    
    return venue, venue != venue_original


def infer_category(category_hint: Optional[str]) -> str:
    """
    Infer event category from category hint.
    Returns: movie, concert, sports, comedy, play, theatre, or uncategorized.
    """
    if not category_hint:
        return "uncategorized"
    
    category_hint_lower = category_hint.lower()
    
    # Check in priority order
    if 'movie' in category_hint_lower or 'film' in category_hint_lower or 'theatrical' in category_hint_lower:
        return 'movie'
    if 'concert' in category_hint_lower or 'live' in category_hint_lower or 'artist' in category_hint_lower:
        return 'concert'
    if 'sports' in category_hint_lower or 'match' in category_hint_lower or 'cricket' in category_hint_lower:
        return 'sports'
    if 'comedy' in category_hint_lower or 'stand-up' in category_hint_lower or 'comedian' in category_hint_lower:
        return 'comedy'
    if 'play' in category_hint_lower or 'theatre' in category_hint_lower or 'musical' in category_hint_lower:
        return 'play'
    
    return 'uncategorized'


def validate_date(date_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if date string is in a proper format.
    Returns (is_valid, normalized_date).
    
    Accepts formats:
    - DD/MM/YYYY
    - MM/DD/YYYY
    - DD-MM-YYYY
    - YYYY-MM-DD
    """
    if not date_str:
        return False, None
    
    # Try DD/MM/YYYY format
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', date_str.strip())
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if 1 <= day <= 31 and 1 <= month <= 12 and 2020 <= year <= 2099:
            return True, f"{day}/{month}/{year}"
    
    # Try MM/DD/YYYY format
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', date_str.strip())
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if 1 <= day <= 31 and 1 <= month <= 12 and 2020 <= year <= 2099:
            return True, f"{month}/{day}/{year}"
    
    return False, None


def validate_time(time_str: str) -> bool:
    """
    Validate if time string is in a proper format.
    Accepts: HH:MM, HHMM
    """
    if not time_str:
        return False
    
    time_str = time_str.strip()
    
    # HH:MM format
    if re.match(r'^\d{1,2}:\d{2}$', time_str):
        hours, mins = map(int, time_str.split(':'))
        return 0 <= hours <= 23 and 0 <= mins <= 59
    
    # HHMM format
    if re.match(r'^\d{4}$', time_str):
        hours, mins = int(time_str[0:2]), int(time_str[2:4])
        return 0 <= hours <= 23 and 0 <= mins <= 59
    
    return False


def parse_amount(amount_str: str) -> Tuple[bool, Optional[float]]:
    """
    Parse and validate amount string.
    Returns (is_valid, parsed_amount).
    
    Accepts formats:
    - ₹1234.56
    - INR 1234.56
    - Rs. 1234.56
    """
    if not amount_str:
        return False, None
    
    # Remove currency symbols and non-numeric chars
    cleaned = re.sub(r'[₹INRrsRsRs\.]\s*', '', amount_str.strip())
    
    # Extract number
    match = re.match(r'^(\d+[,.]\d{2})$', cleaned)
    if match:
        try:
            amount = float(match.group(1).replace(',', ''))
            return True, amount
        except ValueError:
            pass
    
    return False, None


def format_show_datetime(date: str, time: str) -> str:
    """
    Format show date and time into a single datetime string.
    Format: DD/MM/YYYY, HH:MM AM/PM
    """
    if not date and not time:
        return "Not scheduled"
    
    if not date:
        return "TBD"
    
    result = date
    
    if time:
        time = time.strip()
        
        # Handle 24-hour format (00-23)
        if re.match(r'^\d{2}:\d{2}$', time):
            parts = time.split(':')
            hour, minute = int(parts[0]), int(parts[1])
            
            period = "AM" if hour < 12 else "PM"
            if hour >= 12:
                hour = hour - 12
            elif hour < 12:
                period = "AM"
            
            result = f"{date}, {hour:02d}:{minute:02d} {period}"
        else:
            result = f"{date}, {time}"
    
    return result


def extract_year_from_date(date: str) -> Optional[int]:
    """
    Extract year from date string.
    Returns year as integer (4-digit).
    """
    if not date:
        return None
    
    # Match any 4-digit year in date
    match = re.search(r'(\d{4})', date)
    if match:
        year = int(match.group(1))
        if 2020 <= year <= 2099:
            return year
    
    return None


def get_category_color(category: str) -> str:
    """
    Get Tailwind-style color for category.
    Used for ticket card badges and filters.
    """
    colors = {
        'movie': 'bg-purple-100 text-purple-800',
        'concert': 'bg-pink-100 text-pink-800',
        'sports': 'bg-green-100 text-green-800',
        'comedy': 'bg-yellow-100 text-yellow-800',
        'play': 'bg-blue-100 text-blue-800',
        'theatre': 'bg-indigo-100 text-indigo-800',
        'uncategorized': 'bg-gray-100 text-gray-600',
    }
    
    return colors.get(category, colors['uncategorized'])


def get_category_icon(category: str) -> str:
    """
    Get category icon/emoji for visual display.
    """
    icons = {
        'movie': '🎬',
        'concert': '🎸',
        'sports': '⚽',
        'comedy': '🎤',
        'play': '🎭',
        'theatre': '🎭',
        'uncategorized': '❓',
    }
    
    return icons.get(category, '❓')


def truncate_string(text: str, max_length: int = 50) -> str:
    """
    Truncate string to max length, adding ellipsis if needed.
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + '...'


def group_tickets_by_date(tickets: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group tickets by show date.
    """
    grouped = {}
    for ticket in tickets:
        date = ticket.get('show_date')
        if date:
            grouped[date] = grouped.get(date, [])
            grouped[date].append(ticket)
        else:
            grouped['TBD'] = grouped.get('TBD', [])
            grouped['TBD'].append(ticket)
    
    return grouped


def group_tickets_by_venue(tickets: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group tickets by venue.
    """
    grouped = {}
    for ticket in tickets:
        venue = ticket.get('venue')
        if venue:
            venue = venue.lower()
            grouped[venue] = grouped.get(venue, [])
            grouped[venue].append(ticket)
    
    return grouped


def calculate_total_spend(tickets: List[Dict]) -> float:
    """
    Calculate total spend across all tickets.
    """
    return sum(t.get('amount_paid', 0) for t in tickets if t.get('amount_paid'))


def get_ticket_summary(tickets: List[Dict]) -> Dict:
    """
    Generate summary statistics for tickets.
    """
    summary = {
        'total_tickets': len(tickets),
        'by_category': {},
        'total_spend': 0,
        'unique_venues': set(),
        'date_range': {'earliest': None, 'latest': None},
    }
    
    for ticket in tickets:
        # By category
        cat = ticket.get('category', 'uncategorized')
        summary['by_category'][cat] = summary['by_category'].get(cat, 0) + 1
        
        # Total spend
        if ticket.get('amount_paid'):
            summary['total_spend'] += ticket['amount_paid']
        
        # Unique venues
        venue = ticket.get('venue')
        if venue:
            summary['unique_venues'].add(venue)
        
        # Date range
        date = ticket.get('show_date')
        if date:
            if not summary['date_range']['earliest'] or date < summary['date_range']['earliest']:
                summary['date_range']['earliest'] = date
            if not summary['date_range']['latest'] or date > summary['date_range']['latest']:
                summary['date_range']['latest'] = date
    
    summary['unique_venues'] = len(summary['unique_venues'])
    summary['avg_ticket_value'] = summary['total_spend'] / summary['total_tickets'] if summary['total_tickets'] > 0 else 0
    
    return summary