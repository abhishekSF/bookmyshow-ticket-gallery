# BookMyShow Ticket Gallery + Salesforce Headless 360
## Complete Project Handoff Document

**Project**: Build a ticket gallery that scrapes BookMyShow booking emails from Gmail, parses them into structured records, displays them in a React gallery, and pushes records to Salesforce via Headless 360 / Data API.

**Current Status**: Python scraper and React frontend complete. Salesforce integration module planned but not implemented.

**Created**: 2026-08-17

---

## 🎯 Project Goal

- Scrape BookMyShow booking confirmation emails from Gmail
- Parse emails into structured ticket records (event, venue, date, seats, poster art)
- Display tickets in an aesthetic React gallery
- Use locally-run LLM (Ollama) for text cleanup/enrichment only (NOT primary extraction)
- Push records to Salesforce Dev Org via Headless 360 API/MCP surface
- Demo relevant for LMP (Low-Code/Meta-Platform) work

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Gmail API                              │
│                     (Oauth2, readonly scope)                    │
└─────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Python Scraper                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ gmail_client.py - Gmail API wrapper                      │    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Ollama client - Local LLM for enrichment                │    │
│  │ - llama3.1:8b / qwen2.5:7b-instruct                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Ticket parser - HTML parsing + regex                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ TMDb API client - Poster fallback for movies            │    │
│  └─────────────────────────────────────────────────────────┘    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     tickets.json                                │
│  Structured dataset of parsed ticket records                    │
│  { booking_id, event_name, venue, date, time, seats,          │
│    amount_paid, poster_url, category, confidence_score }       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     React Gallery Frontend                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Vite + React + Tailwind CSS                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ TicketCard.jsx - Card design with poster, venue, etc.  │    │
│  └─────────────────────────────────────────────────────────┘    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Salesforce Dev Org                          │
│                    Headless 360 / Data API v61.0                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ SalesForceHeadlessClient - Salesforce integration       │    │
│  │ - OAuth 2.0 authentication                              │    │
│  │ - Transform tickets to Salesforce format                │    │
│  │ - Batch insert via /sobjects/Ticket__c/batch           │    │
│  └─────────────────────────────────────────────────────────┘    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

**Note on Backend**: No live backend needed for v1. Ollama is called offline by Python scraper only. React frontend reads static tickets.json. No CORS issues.

---

## 📂 Workspace Structure

```
bookmyshow-ticket-gallery/
├── .env.example                     # Environment variables template
├── config.py                        # Shared settings (not yet created)
├── python-scraper/                  # Python scraping backend
│   ├── config.py                    # Project settings from env vars
│   ├── gmail_client.py             # Gmail API wrapper
│   ├── ollama_client.py            # Ollama LLM client
│   ├── scraper.py                  # Main scraping logic
│   ├── main_scraper.py            # Entry point
│   └── requirements.txt            # Python dependencies
├── react-app/                       # React frontend
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── public/
│   │   └── tickets.json            # Sample ticket data
│   └── src/
│       ├── index.js
│       ├── App.css
│       ├── App.jsx
│       └── utils/
│           └── ticketHelpers.js    # React utilities
├── shared-config/                   # Shared utilities
│   └── ticket_helpers.py           # Python utilities (date parsing, etc.)
└── salesforce-headless/             # NOT YET CREATED
    ├── requirements.txt            # TBD
    ├── salesforce_config.py        # TBD
    ├── setup_salesforce_oauth.py   # TBD
    └── salesforce_headless.py      # TBD
```

---

## 📦 Tech Stack (All Free)

| Component | Technology | Purpose |
|-----------|------------|---------|
| Email Fetching | Gmail API (google-api-python-client) | OAuth2, readonly scope |
| Python | Python 3.10+ | Scraper, API clients |
| Libraries | beautifulsoup4, regex, google-auth, google-auth-oauthlib | HTML parsing, OAuth |
| LLM (Local) | Ollama + llama3.1:8b / qwen2.5:7b-instruct | Text cleanup, enrichment only |
| Poster Art | TMDb API (free tier) | Fallback for movie posters |
| Frontend | React + Vite + Tailwind CSS | Ticket gallery UI |
| Database | JSON (local) | No backend needed for v1 |
| Salesforce | Dev Org + Data API v61.0 | Push records |
| Analytics | Tableau Public (optional) | Spend/genre/venue dashboards |

---

## 🔑 Key Decisions

### ✅ Primary Extraction = Deterministic (NOT LLM)
**Reason**: BookMyShow emails are templated HTML with consistent, parseable fields. Regex/BeautifulSoup extraction is deterministic and won't hallucinate dates, seat numbers, or amounts.

**LLM (Ollama) is ONLY for:**
- Cleaning inconsistent venue name strings
- Inferring genre/category from title
- Writing one-line blurb per event
- Resolving ambiguous cases flagged as low-confidence by parser

### ✅ Salesforce Integration = Standard Data API v61.0
**Reasoning**:
1. Headless 360 beta may not have data operations ready (announced TDX 2026, July 2026+)
2. Standard Data API is stable and well-documented
3. Demonstrates "headless" pattern even with traditional API
4. Works with any Salesforce org (scratch, sandbox, production)
5. Can evolve to Headless MCP in future v2

### ✅ OAuth 2.0 Authorization Code Grant
**Reasoning**:
- Best for server-side Python integration
- Requires user context (unlike Bearer Token flow)
- Can use either scripted or manual setup

### ✅ Date Format Transformation
**Indian format**: `15 January 2025, 06:30 PM` → **ISO format**: `2025-01-15T06:30:00`

---

## 📋 Salesforce Custom Object Fields (`Ticket__c`)

| Salesforce Field | Type | Source from tickets.json | Constraints |
|-----------------|------|-------------------------|-------------|
| Event_Name__c | String (255) | `event_name` | Truncate to 255 |
| Venue__c | String (255) | `venue` | Truncate to 255 |
| Show_Date__c | DateTime | `show_date` + `show_time` | Format: `YYYY-MM-DD HH:MM:SS` |
| Show_Time__c | Time (24-hour) | `show_time` | Optional if in DateTime |
| Seats__c | String (50) | `seats` | Truncate to 50 |
| Booking_Id__c | String (255) | `booking_id` | **External ID for upsert** |
| Amount__c | Currency | `amount_paid` | `{ "value": 1800, "currencyCode": "INR" }` |
| Poster_URL__c | String (255) | `poster_url` | Truncate to 255 |
| Category__c | Picklist | `category` | Must be valid picklist value |
| Status__c | Picklist | Auto-generated | `'Created'` or `'Failed'` |
| External_id__c | Text (External ID) | `booking_id` | **Required for upsert** |
| CreatedBy__c | Text | API | `'Headless 360 API'` |

---

## 📁 Sample Ticket Data (tickets.json)

15 sample tickets representing different categories:

| Booking ID | Event Name | Venue | Date | Time | Category | Amount |
|------------|------------|-------|------|------|----------|--------|
| BM20250115-001 | Dangal (Movie) | PVR Juhu | 15 January 2025 | 06:30 PM | movie | 1800 |
| BM20250120-002 | Badhaai Ho - Live Concert | Max Studio | 20 January 2025 | 07:30 PM | concert | 3500 |
| BM20250125-003 | Indian Premier League 2025 | Wankhede Stadium, Mumbai | 25 January 2025 | 03:30 PM | sports | 12500 |
| BM20250201-004 | The Complete Works of Shakespeare | Prithvi Theatre | 01 February 2025 | 07:00 PM | play | 1200 |
| BM20250210-005 | Vir Das: The Big Crawl | Phoenix MarketCity | 10 February 2025 | 08:00 PM | comedy | 2800 |
| BM20250214-006 | Sonic the Hedgehog 2 (Movie) | INOX Bandra | 14 February 2025 | 06:00 PM | movie | 5400 |
| BM20250305-007 | Rockstar: The Live Experience | NSCI Dome | 05 March 2025 | 07:30 PM | concert | 8900 |
| BM20250315-008 | Mumbai Indians vs Chennai Super Kings | Arambai Stadium, Mumbai | 15 March 2025 | 03:30 PM | sports | 9800 |
| BM20250320-009 | Hamilton (Musical) | Avenue de Ternes | 20 March 2025 | 08:00 PM | theatre | 7500 |
| BM20250401-010 | The Lion King (Musical) | Rajiv Chowk Theatre | 01 April 2025 | 07:30 PM | theatre | 3200 |
| BM20250410-011 | Taarak Mehta Ka Ooltah Chashma | Film Centre, Mumbai | 10 April 2025 | 06:30 PM | comedy | 1500 |
| BM20250420-012 | Formula 1 Indian Grand Prix | Buddhi Circuit, New Delhi | 20 April 2025 | 05:30 PM | sports | 45000 |
| BM20250501-013 | Jawan (Movie) | PVR Powai | 01 May 2025 | 06:00 PM | movie | 2100 |
| BM20250515-014 | Coldplay Live in Mumbai | Sawai Gandharva Auditorium | 15 May 2025 | 07:30 PM | concert | 18500 |
| BM20250601-015 | Kabir Singh: I Will Not Return | Cinepolis Bandra | 01 June 2025 | 08:30 PM | movie | 3600 |

---

## 🔧 Existing Shared Utilities (`shared-config/ticket_helpers.py`)

### Core Functions
- `clean_text(text)` - Remove extra whitespace, newlines
- `normalize_venue_name(venue)` - Remove common suffixes (India, Deluxe, etc.)
- `infer_category(category_hint)` - Infer genre from title
- `validate_date(date_str)` - Validate date format
- `validate_time(time_str)` - Validate time format
- `parse_amount(amount_str)` - Parse and validate amount
- `format_show_datetime(date, time)` - Format as "DD/MM/YYYY, HH:MM AM/PM"
- `extract_year_from_date(date)` - Extract 4-digit year
- `get_category_color(category)` - Tailwind-style color
- `truncate_string(text, max_length)` - Truncate with ellipsis
- `group_tickets_by_date(tickets)` - Group by date
- `group_tickets_by_venue(tickets)` - Group by venue
- `calculate_total_spend(tickets)` - Sum of all amounts
- `get_ticket_summary(tickets)` - Statistics generator

---

## ⏳ Pending Decisions (Before Implementation)

### 1. Salesforce Integration API Choice

| Option | Status | Recommendation |
|--------|--------|---------------|
| **Standard Data API v61.0** | ✅ Stable | **RECOMMENDED** |
| Headless 360 MCP | ⏳ Beta | Not ready for data ops |

**Why Standard Data API?**
- Announced TDX 2026, beta available July 2026+
- Currently limited to Setup tasks
- No data operations available yet
- Standard Data API is stable and well-documented
- Demonstrates "headless" pattern even with traditional API
- Can evolve to Headless MCP in future v2

### 2. OAuth Setup Method

| Option | Trade-offs | Recommendation |
|--------|------------|---------------|
| **Scripted Setup** (`setup_salesforce_oauth.py`) | Fully automated, reusable | **RECOMMENDED** |
| Manual Setup | User follows instructions, copies tokens | More work for one-time demo |

**Scripted Setup Flow:**
1. Create Connected App in Salesforce (External Client Apps)
2. Script requests auth code from user browser
3. Script exchanges code for refresh token
4. Save tokens to `tokens/sf_tokens.json`

### 3. Include Sample Data

| Option | Recommendation |
|--------|---------------|
| ✅ **Include Mock Data** | Test immediately without Gmail setup |
| ⏳ Real Data Only | Requires working Gmail OAuth |

**Decision**: Include 15 sample tickets for demo purposes

---

## 📄 Files to Create

### `/salesforce-headless/` Directory

#### 1. `requirements.txt`
```txt
requests>=2.31.0
simple-salesforce>=1.11.0
json5>=0.9.12
python-dotenv>=1.0.0
```

#### 2. `salesforce_config.py`
```python
"""Salesforce configuration settings."""
import os

class SalesforceSettings:
    """Salesforce connection settings."""
    
    sf_url: str = os.getenv("SF_URL", "https://test-dev-ed.sfdc.us")
    sf_api_version: str = os.getenv("SF_API_VERSION", "v61.0")
    sf_api_url: str = f"{sf_url}/services/data/{sf_api_version}"
    sf_enabled: bool = os.getenv("SF_ENABLE", "false").lower() == "true"
    sf_tenant_id: Optional[str] = os.getenv("SF_TENANT_ID")
    
    @property
    def oauth_base_url(self) -> str:
        """Base URL for OAuth endpoints."""
        return f"https://{self.sf_url}.salesforce.com"
```

#### 3. `setup_salesforce_oauth.py`
```python
"""Script to set up Salesforce OAuth 2.0 credentials."""
# Flow:
# 1. Create Connected App in Salesforce (External Client Apps)
# 2. Run script - it will open browser for auth code
# 3. Enter auth code
# 4. Script exchanges code for refresh token
# 5. Save tokens to tokens/sf_tokens.json
```

#### 4. `salesforce_headless.py`
```python
"""Salesforce Headless integration module."""
from datetime import datetime
import json
from typing import Dict, List, Optional, Any

class SalesforceHeadlessClient:
    """Client for Salesforce Data API integration."""
    
    def __init__(self, config: SalesforceSettings, token_file: str):
        self.config = config
        self.token_file = token_file
        self.access_token = None
        self.token_expires = None
        
    def authenticate(self):
        """OAuth 2.0 Authorization Code Grant flow."""
        # Step 1: Generate auth URL
        auth_url = self._build_auth_url()
        # Step 2: Open browser for user to enter auth code
        # Step 3: Exchange auth code for tokens
        # Step 4: Save tokens to file
        
    def get_access_token(self) -> str:
        """Get or refresh access token."""
        if self.access_token and not self._is_token_expired():
            return self.access_token
        # Refresh token
        token = self._refresh_token()
        self._save_token(token)
        return token.access_token
        
    def transform_tickets_for_salesforce(
        self, tickets: List[Dict]
    ) -> List[Dict]:
        """
        Transform tickets.json to Salesforce format.
        Handles date formatting, currency structuring, validation.
        """
        transformed = []
        for ticket in tickets:
            sf_record = self._transform_ticket(ticket)
            sf_record["External_id__c"] = ticket.get("booking_id")
            sf_record["Status__c"] = "Created"
            transformed.append(sf_record)
        return transformed
        
    def _transform_ticket(self, ticket: Dict) -> Dict:
        """Transform single ticket record."""
        # Transform date from Indian format to ISO
        show_date = self._transform_date(ticket.get("show_date"), ticket.get("show_time"))
        
        # Transform currency
        amount_obj = self._transform_currency(ticket.get("amount_paid"))
        
        return {
            "Event_Name__c": self._transform_field(ticket.get("event_name")),
            "Venue__c": self._transform_field(ticket.get("venue")),
            "Show_Date__c": show_date,
            "Seats__c": ticket.get("seats"),
            "Booking_Id__c": ticket.get("booking_id"),
            "Amount__c": amount_obj,
            "Poster_URL__c": ticket.get("poster_url"),
            "Category__c": ticket.get("category"),
            "Amount__c": amount_obj,
        }
        
    def batch_insert_records(self, records: List[Dict]) -> Dict:
        """Batch insert records (max 50 per batch)."""
        # Split into batches of 50
        batches = [records[i:i+50] for i in range(0, len(records), 50)]
        results = []
        for batch in batches:
            result = self._insert_batch(batch)
            results.extend(result.get("results", []))
        return {"results": results}
        
    def _insert_batch(self, records: List[Dict]) -> Dict:
        """Insert a batch of records."""
        url = f"{self.config.sf_api_url}/sobjects/Ticket__c/batch"
        payload = {
            "jobId": None,
            "records": [{"sObjectType": "Ticket__c", "data": r} for r in records],
            "actionLabel": "Created"
        }
        response = self._post_request(url, payload)
        return response
        
    def check_batch_status(self, job_id: str) -> Dict:
        """Check batch job results."""
        url = f"{self.config.sf_api_url}/jobs/{job_id}/results"
        return self._post_request(url, {})
        
    def delete_all_records(self, filter_query: str = None):
        """Delete all Ticket__c records."""
        url = f"{self.config.sf_api_url}/sobjects/Ticket__c/batch"
        payload = {
            "jobId": None,
            "records": [{"sObjectType": "Ticket__c", "data": {"$query": {"SELECT": "*", "WHERE": f"{filter_query}"}}} for _ in range(1000)],
            "actionLabel": "Deleted",
            "operation": "delete"
        }
        return self._post_request(url, payload)
```

#### 5. `tokens/sf_tokens.json`
```json
{
  "instance_url": "https://test-dev-ed.sfdc.us",
  "access_token": "00 invalid...",
  "refresh_token": "00 invalid...",
  "instance_type": "PartiallyInvalid",
  "is_jwt": false
}
```

#### 6. `README.md`
```markdown
# Salesforce Headless Integration Module

## Overview
This module integrates with Salesforce Data API v61.0 to push ticket records
from the BookMyShow ticket scraper into a Salesforce Dev Org.

## Architecture
```
tickets.json -> SalesforceHeadlessClient -> Salesforce (Ticket__c records)
```

## Prerequisites
1. Salesforce Dev Org (scratch/sandbox/production)
2. Connected App created in Salesforce (External Client Apps)
3. Custom Object `Ticket__c` with required fields
4. Python 3.10+ with dependencies installed

## Setup

### Step 1: Create Salesforce Connected App
1. Go to Salesforce Setup
2. Navigate to "External Client Apps"
3. Click "New Connected App"
4. Fill in details:
   - API Name: BookMyShow Integration
   - API (Consumer) Key: [leave blank, script will generate]
   - Consumer Secret: [leave blank, script will generate]
   - OAuth Settings:
     - OAuth Scopes: OAuthscopes:api (or just OAuth scopes: none for testing)
   - Access Control Settings: Access Control Mode = No Login Required
   - Callback URL: http://localhost:5173 (or your frontend URL)
5. Click "Save"
6. Note the **Consumer Key** and **Consumer Secret**

### Step 2: Run OAuth Setup Script
```bash
cd salesforce-headless
python setup_salesforce_oauth.py
```
- Follow browser prompts to enter auth code
- Tokens will be saved to `tokens/sf_tokens.json`

### Step 3: Configure Environment Variables
```bash
# Copy .env.example to .env and fill in credentials
cp .env.example .env

# Edit with your Salesforce credentials:
SF_URL=test-dev-ed.sfdc.us
SF_CLIENT_ID=your-sfdc-connected-app-client-id
SF_CLIENT_SECRET=your-sfdc-connected-app-client-secret
SF_ENABLE=true
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Run Integration
```bash
python salesforce_headless.py
```

## Usage

### Push Records to Salesforce
```bash
# Ensure tokens/sf_tokens.json exists
# Ensure tickets.json is ready
python salesforce_headless.py
```

### Debug/Re-run with Different Data
```bash
# Delete existing records
python delete_records.py

# Push new records
python salesforce_headless.py
```

## API Details

### Record Fields Mapping

| Salesforce Field | Type | Source | Constraints |
|-----------------|------|--------|-------------|
| Event_Name__c | String (255) | `event_name` | Truncate to 255 |
| Venue__c | String (255) | `venue` | Truncate to 255 |
| Show_Date__c | DateTime | `show_date` + `show_time` | ISO format: YYYY-MM-DD HH:MM:SS |
| Seats__c | String (50) | `seats` | Truncate to 50 |
| Booking_Id__c | String (255) | `booking_id` | External ID |
| Amount__c | Currency | `amount_paid` | `{ "value": ..., "currencyCode": "INR" }` |
| Category__c | Picklist | `category` | Must be valid value: movie, concert, sports, comedy, play, theatre, uncategorized |
| Status__c | Picklist | Auto | 'Created' or 'Failed' |

### Date Transformation
Indian format: `"15 January 2025"` → ISO format: `"2025-01-15 06:30:00"`

### Currency Transformation
Plain value: `1800` → Salesforce currency: `{"value": 1800, "currencyCode": "INR"}`

## Troubleshooting

### Error: "Invalid session_id"
- Your token has expired
- Re-run: `python setup_salesforce_oauth.py`

### Error: "Invalid access token"
- Connected app credentials mismatch
- Check `SF_CLIENT_ID` and `SF_CLIENT_SECRET` in `.env`

### Error: "Invalid sobject type"
- Custom object `Ticket__c` doesn't exist in your org
- Run this to create it:
```bash
sf object new Ticket__c -d '{"name": "Ticket__c", "label": "Ticket", "apiName": "Ticket__c", "fields": [{"name": "Event_Name__c", "type": "Text", "length": 255}, {"name": "Venue__c", "type": "Text", "length": 255}, {"name": "Show_Date__c", "type": "DateTime"}, {"name": "Seats__c", "type": "Text", "length": 50}, {"name": "Booking_Id__c", "type": "Text", "length": 255, "externalId": "External_id__c"}, {"name": "Amount__c", "type": "Currency"}, {"name": "Poster_URL__c", "type": "Text", "length": 255}, {"name": "Category__c", "type": "Picklist", "picklistValues": [{"value": "movie"}, {"value": "concert"}, {"value": "sports"}, {"value": "comedy"}, {"value": "play"}, {"value": "theatre"}, {"value": "uncategorized"}]}]} -f json
```

### Error: "Record already exists"
- Use upsert instead of insert
- `External_id__c` field matches existing record

## Future Improvements
- Add retry logic for failed records
- Add batch check for failed records
- Add CSV export for Tableau integration
- Add Headless 360 MCP integration (v2)
```

---

## 📋 Next Steps (Implementation Plan)

### Phase 1: Update Environment File
```bash
# Update .env.example with complete Salesforce section
```

### Phase 2: Create Shared Helpers Extension
```bash
# Create: shared-config/ticket_helpers_salesforce.py
# Add Salesforce-specific transformation functions
```

### Phase 3: Create Salesforce Directory Structure
```bash
mkdir -p salesforce-headless/tokens
```

### Phase 4: Create SalesForce Config
**File**: `salesforce-headless/salesforce_config.py`
```python
"""
Salesforce configuration settings for Headless integration.
"""
import os
from typing import Optional

class SalesforceConfig:
    """Configuration for Salesforce Data API integration."""
    
    # Connection settings
    sf_url: str = os.getenv("SF_URL", "https://test-dev-ed.sfdc.us")
    sf_api_version: str = os.getenv("SF_API_VERSION", "v61.0")
    sf_api_url: str = f"{sf_url}/services/data/v61.0"
    
    # OAuth settings
    sf_client_id: Optional[str] = os.getenv("SF_CLIENT_ID", None)
    sf_client_secret: Optional[str] = os.getenv("SF_CLIENT_SECRET", None)
    sf_token_file: str = "./tokens/sf_tokens.json"
    
    # Custom object settings
    sf_custom_object: str = "Ticket__c"
    sf_field_mapping: dict = {
        "Event_Name__c": "event_name",
        "Venue__c": "venue",
        "Show_Date__c": "show_date",
        "Show_Time__c": "show_time",
        "Seats__c": "seats",
        "Booking_Id__c": "booking_id",
        "Amount__c": "amount_paid",
        "Poster_URL__c": "poster_url",
        "Category__c": "category",
        "Status__c": "status",
        "External_id__c": "booking_id"
    }
    
    # Picklist validation
    valid_categories: List[str] = [
        "movie", "concert", "sports", "comedy", "play", "theatre", "uncategorized"
    ]
    
    # Date format (Indian to ISO)
    month_names = {
        "January": "01", "February": "02", "March": "03", "April": "04",
        "May": "05", "June": "06", "July": "07", "August": "08",
        "September": "09", "October": "10", "November": "11", "December": "12"
    }
    
    @property
    def is_enabled(self) -> bool:
        """Check if Salesforce integration is enabled."""
        return os.getenv("SF_ENABLE", "false").lower() == "true"
    
    @property
    def is_auth_valid(self) -> bool:
        """Check if OAuth credentials are valid."""
        return self.sf_client_id is not None and \
               self.sf_client_secret is not None and \
               self.sf_refresh_token is not None
```

### Phase 5: Create Shared Helpers (Salesforce Extension)
**File**: `shared-config/ticket_helpers_salesforce.py`
```python
"""
Salesforce-specific helper functions for ticket transformation.
Extends shared ticket_helpers.py for Salesforce field mapping.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime

def transform_date_for_salesforce(date: str, time: str = None) -> str:
    """
    Transform Indian date format to Salesforce ISO format.
    
    Input formats:
    - DD Month YYYY (e.g., "15 January 2025")
    - DD-MM-YYYY
    
    Output format:
    - YYYY-MM-DD HH:MM:SS (Salesforce DateTime format)
    
    Args:
        date: Date string in Indian format
        time: Time string in "HH:MM AM/PM" or "HH:MM" format
        
    Returns:
        Formatted date string in Salesforce DateTime format
    """
    # ... implementation ...
```

### Phase 6: Create Requirements
**File**: `salesforce-headless/requirements.txt`
```txt
requests>=2.31.0
simple-salesforce>=1.11.0
python-dotenv>=1.0.0
```

### Phase 7: Create OAuth Setup Script
**File**: `salesforce-headless/setup_salesforce_oauth.py`
```python
"""
Script to set up Salesforce OAuth 2.0 credentials.

Steps:
1. User creates Connected App in Salesforce
2. Script opens browser for auth code
3. User enters auth code
4. Script exchanges code for tokens
5. Tokens saved to tokens/sf_tokens.json
"""
```

### Phase 8: Create Main Integration Module
**File**: `salesforce-headless/salesforce_headless.py`
```python
"""
Salesforce Headless Integration Module.

Transforms tickets.json records and pushes to Salesforce via Data API v61.0.
"""
```

### Phase 9: Create Sample Fixtures
**File**: `salesforce-headless/fixtures/sample_tickets.json`
- Copy from `react-app/public/tickets.json` or similar

### Phase 10: Update .env.example
```bash
# Add complete Salesforce section
SF_CLIENT_ID=
SF_CLIENT_SECRET=
SF_REFRESH_TOKEN=
SF_TENANT_ID=
SF_ENABLE=false
```

### Phase 11: Update Main README.md
```bash
# Add Salesforce integration documentation
# Include screenshots, flow diagrams, troubleshooting
```

---

## ⏹️ Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Python Scraper | ✅ Complete | Working in `python-scraper/` |
| React Frontend | ✅ Complete | Working in `react-app/` |
| Shared Config | ✅ Complete | `ticket_helpers.py` exists |
| Salesforce Integration | ⏳ Planned | Directory empty, nothing implemented |
| Environment Variables | 📝 Partial | Needs Salesforce section |

---

## ⚠️ Risks & Caveats

1. **Gmail OAuth Setup** - Most likely time sink (first run opens browser)
2. **BookMyShow Email HTML Variations** - Parser needs per-template branches
3. **Salesforce Custom Object** - `Ticket__c` must be created in target org beforehand
4. **Headless 360 Documentation** - New (announced TDX 2026), may have rough edges
5. **Date Format Conversion** - Indian format to ISO needs careful handling
6. **Currency Format** - Plain value to Salesforce currency structure

---

## 🎯 User Approval Needed

Before implementing, please confirm:

- [ ] **Integration API**: Standard Data API v61.0 (recommended)
- [ ] **OAuth Setup**: Scripted approach (recommended)
- [ ] **Sample Data**: Include 15 mock tickets for demo (recommended)

---

## 📞 Contact

If you have questions about this handoff or need clarification on any decision, please ask before I proceed.