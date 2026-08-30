# 🎫 BookMyShow Ticket Gallery + Salesforce Headless 360

**Project Status:** Python scraper ✅ | React frontend ✅ | Salesforce integration ⏳ Planned  
**Current Working Directory:** `bookmyshow-ticket-gallery/`  
**Last Updated:** `{{ "AUTO-GENERATED" }}`  
**Handoff Agent:** Bionic App  
**Next Agent:** LM Studio

---

## 🎯 Executive Summary

This is a personal demo project that:
1. Scrapes BookMyShow booking confirmation emails from Gmail via Gmail API
2. Parses emails deterministically using regex/BeautifulSoup (NOT LLM for primary extraction)
3. Uses local Ollama LLM (llama3.1:8b or qwen2.5:7b-instruct) only for text cleanup/enrichment
4. Looks up poster art from TMDb API for movie bookings (fallback for non-movies)
5. Displays tickets in an aesthetic React + Tailwind gallery
6. Pushes structured records to Salesforce Dev Org via Headless 360/Data API (NOT YET IMPLEMENTED)

**Current Implementation:** Python scraper and React frontend are complete and working locally.

---

## 📂 Workspace Structure

```
bookmyshow-ticket-gallery/
├── .env.example                          # Environment variables template (Salesforce section: placeholders)
├── config.py                             # Shared settings from env vars (NOT YET CREATED)
├── python-scraper/                       # Python scraping backend ✅ COMPLETE
│   ├── config.py                         # Project settings from env vars
│   ├── gmail_client.py                   # Gmail API wrapper ✅ WORKING
│   ├── ollama_client.py                  # Ollama LLM client ✅ WORKING
│   ├── scraper.py                        # Ticket parser logic ✅ WORKING
│   ├── main_scraper.py                   # Entry point ✅ WORKING
│   └── requirements.txt                  # Python dependencies
│
├── react-app/                            # React frontend ✅ COMPLETE
│   ├── package.json                      # Node dependencies ✅
│   ├── vite.config.js                    # Vite configuration ✅
│   ├── tailwind.config.js               # Tailwind configuration ✅
│   ├── postcss.config.js                 # PostCSS configuration ✅
│   ├── public/
│   │   └── tickets.json                  # Sample ticket data ✅
│   └── src/
│       ├── index.js                      # React entry point ✅
│       ├── App.jsx                       # Main app with routing ✅
│       ├── App.css                       # App styles ✅
│       └── utils/
│           └── ticketHelpers.js          # React utilities ✅
│
├── shared-config/                        # Shared utilities ✅ COMPLETE
│   └── ticket_helpers.py                 # Python utilities (date parsing, etc.)
│
└── salesforce-headless/                  # NOT CREATED
    ├── requirements.txt                  # NOT YET CREATED
    ├── salesforce_config.py              # NOT YET CREATED
    ├── setup_salesforce_oauth.py         # NOT YET CREATED
    ├── salesforce_headless.py            # NOT YET CREATED
    └── tokens/                           # Folder for OAuth tokens
        └── sf_tokens.json                # OAuth credentials (NOT YET CREATED)
```

---

## ✅ What's Been Completed

### 1. Python Scraper (`python-scraper/`) ✅

**Implemented Files:**
| File | Purpose | Status |
|------|---------|--------|
| `config.py` | Loads settings from `.env` file | ✅ Working |
| `gmail_client.py` | Gmail API wrapper for fetching emails | ✅ Working |
| `ollama_client.py` | Local LLM client for text enrichment | ✅ Working |
| `scraper.py` | Ticket parser + TMDb poster fallback | ✅ Working |
| `main_scraper.py` | Entry point orchestrates full pipeline | ✅ Working |
| `requirements.txt` | Python dependencies | ✅ Working |

**Key Features Implemented:**
- Gmail OAuth 2.0 setup via `setup_gmail_oauth.py`
- Deterministic email parsing using regex + BeautifulSoup
- Ollama enrichment for low-confidence extractions (NOT for primary data extraction)
- TMDb API fallback for movie poster art
- Output: `tickets.json` with structured records

**Architecture:**
```
Gmail API → (fetch emails) → Deterministic Parser → Ollama (enrichment only) → TMDb (poster fallback) → tickets.json
```

**Note:** The React frontend reads `tickets.json` directly (no live backend needed). Ollama is called offline by Python script only.

### 2. React Frontend (`react-app/`) ✅

**Implemented Files:**
| File | Purpose | Status |
|------|---------|--------|
| `package.json` | Node.js dependencies | ✅ Working |
| `vite.config.js` | Vite build configuration | ✅ Working |
| `tailwind.config.js` | Tailwind CSS configuration | ✅ Working |
| `postcss.config.js` | PostCSS configuration | ✅ Working |
| `src/index.js` | React entry point | ✅ Working |
| `src/App.jsx` | Main app with routing | ✅ Working |
| `src/App.css` | App styles with Tailwind | ✅ Working |
| `src/components/Gallery.jsx` | Ticket gallery with filters/sort | ✅ Working |
| `src/components/TicketCard.jsx` | Individual ticket card component | ✅ Working |
| `src/components/Loading.jsx` | Loading state component | ✅ Working |
| `src/utils/ticketHelpers.js` | React utilities (date parsing, etc.) | ✅ Working |
| `public/tickets.json` | Sample ticket data | ✅ Present |

**Features:**
- Responsive ticket gallery grid with Tailwind CSS
- Filter by category (movie, concert, sports, comedy, play, theatre)
- Filter by year (extracted from show date)
- Sort by date, amount, name, or alphabetically
- Loading and error states
- Ticket card design with poster image, event details

**Tech Stack:** React 18 + Vite + Tailwind CSS + React Router

### 3. Shared Utilities (`shared-config/`) ✅

**File:** `ticket_helpers.py`

**Available Functions:**
- `clean_text(text)` - Remove extra whitespace, newlines
- `normalize_venue_name(venue)` - Remove common suffixes
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

## ⏳ What's NOT Yet Implemented

### Salesforce Headless Integration (`salesforce-headless/`) ❌ NOT CREATED

**This directory does not exist yet.** The following files need to be created:

| File | Purpose | Status |
|------|---------|--------|
| `requirements.txt` | Python dependencies | ❌ NEEDS CREATION |
| `salesforce_config.py` | Salesforce connection settings | ❌ NEEDS CREATION |
| `setup_salesforce_oauth.py` | OAuth 2.0 setup script | ❌ NEEDS CREATION |
| `salesforce_headless.py` | Main Salesforce integration module | ❌ NEEDS CREATION |
| `tokens/` | Folder for OAuth token storage | ❌ NEEDS CREATION |
| `fixtures/sample_tickets.json` | Sample data for testing | ❌ OPTIONAL |

**Key Decisions to Confirm Before Implementation:**

#### 1. Salesforce Integration API Choice

| Option | Status | Recommendation |
|--------|--------|---------------|
| **Standard Data API v61.0** | ✅ Stable | **✅ RECOMMENDED** |
| Headless 360 MCP | ⏳ Beta | ❌ NOT READY (announced TDX 2026) |

**Why Standard Data API v61.0?**
- Headless 360 beta announced at TDX 2026, only available July 2026+
- Currently limited to Setup tasks
- No data operations available yet
- Standard Data API is stable and well-documented
- Works with any Salesforce org (scratch, sandbox, production)
- Can evolve to Headless MCP in future v2

#### 2. OAuth Setup Method

| Option | Trade-offs | Recommendation |
|--------|------------|---------------|
| **Scripted Setup** (`setup_salesforce_oauth.py`) | Fully automated, reusable | **✅ RECOMMENDED** |
| Manual Setup | User follows instructions, copies tokens | More work for one-time demo |

**Scripted Setup Flow:**
1. Create Connected App in Salesforce (External Client Apps)
2. Script requests auth code from user browser
3. Script exchanges code for refresh token
4. Save tokens to `tokens/sf_tokens.json`

#### 3. Include Sample Data

| Option | Recommendation |
|--------|---------------|
| ✅ **Include Mock Data** | Test immediately without Gmail setup |
| ⏳ Real Data Only | Requires working Gmail OAuth |

**Decision:** Include 15 sample tickets for demo purposes

---

## 🔑 Technical Decisions & Architecture

### Primary Extraction = Deterministic (NOT LLM)

**Reasoning:**
- BookMyShow emails are templated HTML with consistent, parseable fields
- Regex/BeautifulSoup extraction is deterministic and won't hallucinate dates, seat numbers, or amounts
- Using LLM for primary extraction would risk data corruption

**LLM (Ollama) is ONLY for:**
- Cleaning inconsistent venue name strings
- Inferring genre/category from title
- Writing one-line blurb per event
- Resolving ambiguous cases flagged as low-confidence by parser

### Salesforce Custom Object Fields (`Ticket__c`)

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

**Category Picklist Values:**
- `movie`
- `concert`
- `sports`
- `comedy`
- `play`
- `theatre`
- `uncategorized`

### Date Transformation

**Indian format → Salesforce ISO format:**
- Input: `"15 January 2025"`
- Output: `"2025-01-15 06:30:00"`

### Currency Transformation

**Plain value → Salesforce currency structure:**
- Input: `1800`
- Output: `{"value": 1800, "currencyCode": "INR"}`

### Sample Ticket Data (15 records)

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

## 📋 Next Steps (Implementation Plan)

### Phase 1: Update Environment File

**File:** `.env.example`

**Action:** Add/verify complete Salesforce section with explanations:

```ini
# Salesforce Headless / Data API Integration (Optional)
SF_URL=https://test-dev-ed.sfdc.us
SF_API_VERSION=v61.0
SF_CLIENT_ID=your-sfdc-connected-app-client-id
SF_CLIENT_SECRET=your-sfdc-connected-app-client-secret
SF_REFRESH_TOKEN=your-sfdc-refresh-token
SF_TENANT_ID=your-sfdc-tenant-id  # Format: 0DExxxxxxxxxxxxxxxxxx
SF_ENABLE=false  # Set to true after OAuth setup to enable
```

### Phase 2: Create Salesforce Headless Directory

```bash
mkdir -p bookmyshow-ticket-gallery/salesforce-headless/tokens
mkdir -p bookmyshow-ticket-gallery/salesforce-headless/fixtures
```

### Phase 3: Create SalesForce Config

**File:** `salesforce-headless/salesforce_config.py`

**Purpose:** Configuration settings for Salesforce Data API integration

**Key Settings:**
```python
sf_url: str = os.getenv("SF_URL", "https://test-dev-ed.sfdc.us")
sf_api_version: str = os.getenv("SF_API_VERSION", "v61.0")
sf_api_url: str = f"{sf_url}/services/data/v61.0"
sf_client_id: Optional[str]
sf_client_secret: Optional[str]
sf_refresh_token: Optional[str]
sf_tenant_id: Optional[str]  # Format: 0DExxxxxxxxxxxxxxxxxx
sf_custom_object: str = "Ticket__c"
sf_enable: bool = False
```

**Required Helper Functions:**
- `transform_date_for_salesforce(date, time)` - Convert Indian format to ISO
- `transform_currency_for_salesforce(amount)` - Convert to `{value, currencyCode}` struct
- `transform_field(text, max_length=255)` - Truncate and clean text
- `transform_datetime(date, time)` - Combine date/time into ISO format

### Phase 4: Create OAuth Setup Script

**File:** `salesforce-headless/setup_salesforce_oauth.py`

**Purpose:** Set up Salesforce OAuth 2.0 credentials

**Flow:**
1. Check if `tokens/sf_tokens.json` exists and is valid
2. If not, generate OAuth URL and open in browser
3. User enters auth code
4. Exchange auth code for tokens
5. Save tokens to `tokens/sf_tokens.json`

**Steps for User:**
1. Create Connected App in Salesforce (Setup → API → External Client Apps → New Connected App)
   - Name: "BookMyShow Integration"
   - OAuth Scopes: "OAuth scopes: api" (or "none" for testing)
   - Access Control Mode: "No Login Required"
   - Callback URL: `http://localhost:5173` or your frontend URL
2. Run `python setup_salesforce_oauth.py`
3. Follow browser prompts, enter auth code
4. Script saves tokens to `tokens/sf_tokens.json`
5. Edit `.env.example` with actual credentials

### Phase 5: Create Salesforce Integration Module

**File:** `salesforce-headless/salesforce_headless.py`

**Purpose:** Transform tickets and push to Salesforce via Data API

**Class:** `SalesforceHeadlessClient`

**Methods:**
```python
def __init__(self, config: SalesforceConfig, token_file: str)
def authenticate(self)  # OAuth 2.0 Authorization Code Grant
def get_access_token(self)  # Get or refresh access token
def transform_tickets_for_salesforce(tickets: List[Dict]) -> List[Dict]  # Transform for SF
def _transform_ticket(ticket: Dict) -> Dict  # Transform single ticket
def batch_insert_records(records: List[Dict]) -> Dict  # Batch insert (max 50 per batch)
def _insert_batch(records: List[Dict]) -> Dict  # Insert/Upsssert single batch
def check_batch_status(job_id: str) -> Dict  # Check batch job results
def delete_all_records(self, filter_query: str = None)  # Cleanup for re-runs
```

**Key Transformations:**
- Date: `15 January 2025` → `2025-01-15T06:30:00` (ISO format for DateTime field)
- Currency: `1800` → `{"value": 1800, "currencyCode": "INR"}`
- Category: Validate against picklist values, map invalid to `uncategorized`
- Date/Time: Use `format_show_datetime()` to combine into single DateTime string

**API Endpoint:** `/services/data/v61.0/sobjects/Ticket__c/batch`

**Batching:** Split into batches of 50 records max (Salesforce limit)

**Upsert Logic:** Use `External_id__c` (booking_id) for upsert instead of insert to avoid duplicates

### Phase 6: Create Requirements

**File:** `salesforce-headless/requirements.txt`

```txt
requests>=2.31.0
simple-salesforce>=1.11.0
python-dotenv>=1.0.0
```

### Phase 7: Add Sample Tickets

**File:** `salesforce-headless/fixtures/sample_tickets.json`

**Action:** Copy from `react-app/public/tickets.json`

**Purpose:** Test Salesforce integration without needing real Gmail data

### Phase 8: Update .env.example

**File:** `.env.example`

**Add Salesforce section:**
```ini
# Salesforce Data API v61.0 (Optional - for pushing records)
SF_URL=https://test-dev-ed.sfdc.us
SF_API_VERSION=v61.0
SF_CLIENT_ID=your-sfdc-connected-app-client-id
SF_CLIENT_SECRET=your-sfdc-connected-app-client-secret
SF_REFRESH_TOKEN=your-sfdc-refresh-token
SF_TENANT_ID=your-sfdc-tenant-id
SF_ENABLE=false  # Set to true after OAuth setup

# Salesforce Custom Object: Ticket__c
# Fields: Event_Name__c, Venue__c, Show_Date__c, Seats__c, 
#        Booking_Id__c (External_id), Amount__c, Poster_URL__c, Category__c, Status__c
```

---

## 🔍 Key Implementation Details

### Date Transformation (Indian → Salesforce ISO)

**Input Format:** `"15 January 2025, 06:30 PM"`

**Expected Output:** `"2025-01-15T06:30:00.000Z"`

**Helper Function:**
```python
def transform_date_to_iso(date_str: str, time_str: str = None) -> str:
    """
    Convert Indian date format to ISO 8601.
    
    Input: "15 January 2025, 06:30 PM"
    Output: "2025-01-15T06:30:00.000Z"
    """
    # Extract date and time components
    date_part = date_str.split(',')[0].strip()  # "15 January 2025"
    time_part = time_str.strip() if time_str else None
    
    # Parse date
    match = re.match(r'^(\d{1,2})\s+(\w+)\s+(\d{2,4})$', date_part)
    day = int(match.group(1))
    month_name = match.group(2)
    year = int(match.group(3))
    
    # Convert month name to number
    months = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    month = months[month_name]
    
    # Format to ISO
    date_iso = f"{year:04d}-{month:02d}-{day:02d}"
    
    # Parse time (handle AM/PM)
    if time_part:
        am_pm = time_part[-2:] if len(time_part) >= 2 else ''
        time_main = time_part[:-2] if am_pm else time_part
        if am_pm.upper() == 'PM' and time_main != '12':
            hours = int(time_main) + 12
        elif am_pm.upper() == 'AM' and time_main == '12':
            hours = 0
        else:
            hours = int(time_main)
        mins = int(time_part[-2:]) if len(time_part) > 4 else 0
        time_iso = f"{hours:02d}:{mins:02d}:00"
    else:
        time_iso = "00:00:00"
    
    return f"{date_iso}T{time_iso}.000Z"
```

### Currency Transformation (Plain → Salesforce)

**Input:** `1800` or `"1800"` or `{"value": 1800}` (already transformed)

**Output:** `{"value": 1800, "currencyCode": "INR"}`

**Helper Function:**
```python
def transform_currency_to_salesforce(amount: float) -> Dict:
    """
    Transform plain amount to Salesforce Currency format.
    
    Input: 1800
    Output: {"value": 1800, "currencyCode": "INR"}
    """
    return {
        "value": int(amount),
        "currencyCode": "INR"
    }
```

### Data API Request Format

**Endpoint:** `POST /services/data/v61.0/sobjects/Ticket__c/batch`

**Request Body:**
```json
{
  "jobId": null,
  "records": [
    {"sObjectType": "Ticket__c", "data": {
        "Event_Name__c": "Dangal (Movie)",
        "Venue__c": "PVR Juhu",
        "Show_Date__c": "2025-01-15T06:30:00.000Z",
        "Seats__c": "2A",
        "Booking_Id__c": "BM20250115-001",
        "Amount__c": {"value": 1800, "currencyCode": "INR"},
        "Poster_URL__c": "https://image.tmdb.org/...",
        "Category__c": "movie",
        "Status__c": "Created"
    }},
    ...
  ],
  "actionLabel": "Created"
}
```

**Response:**
```json
{
  "jobId": "0Dxxxx...",
  "done": false,
  "totalSize": 15,
  "results": [...]
}
```

---

## 📋 Files to Create (Summary)

### Priority 1 - Required Files

| File | Status | Description |
|------|--------|-------------|
| `config.py` | ✅ Already exists | Shared settings from env vars |
| `salesforce-headless/` | ❌ NOT CREATED | Directory for Salesforce integration |
| `salesforce-headless/salesforce_config.py` | ❌ NEEDS CREATION | Salesforce connection settings |
| `salesforce-headless/setup_salesforce_oauth.py` | ❌ NEEDS CREATION | OAuth 2.0 setup script |
| `salesforce-headless/salesforce_headless.py` | ❌ NEEDS CREATION | Main integration module |
| `tokens/` | ❌ NEEDS CREATION | Directory for OAuth token storage |
| `.env.example` | ✅ Exists but needs update | Add Salesforce credentials section |

### Priority 2 - Optional Enhancements

| File | Status | Description |
|------|--------|-------------|
| `shared-config/ticket_helpers_salesforce.py` | ⏳ CAN BE CREATED | Salesforce-specific transformation helpers |
| `salesforce-headless/fixtures/sample_tickets.json` | ⏳ CAN BE CREATED | Sample data for testing |
| `salesforce-headless/delete_records.py` | ⏳ CAN BE CREATED | Utility to clean up test records |

---

## ⚠️ Risks & Caveats

### High Priority

1. **Gmail OAuth Setup** - Most likely time sink. First run opens browser for consent. Takes 5-10 minutes.

2. **Salesforce Custom Object** - `Ticket__c` must be created in target Salesforce org BEFORE running integration.
   - If missing, API will return "Invalid sobject type" error
   - Provide `sf object new` command to create the object

3. **Salesforce OAuth Setup** - Requires creating Connected App in Salesforce Setup. Takes 5-10 minutes first time.

4. **Date Format Conversion** - Indian format (`15 January 2025`) → Salesforce ISO format (`2025-01-15T06:30:00.000Z`). Must be precise.

5. **Currency Format** - Plain value (`1800`) → Salesforce structure (`{"value": 1800, "currencyCode": "INR"}`). Must be precise.

### Medium Priority

6. **BookMyShow Email HTML Variation** - Parser needs per-template branches for different booking types (movies vs events vs sports).

7. **Headless 360 Beta Docs** - If you want to use Headless 360 MCP instead of Data API, docs are new (announced TDX 2026). May have rough edges.

### Low Priority

8. **Salesforce OAuth Tokens** - Need to be refreshed periodically (access tokens expire, need refresh token).

9. **Batch Size Limit** - Salesforce limits to 50 records per batch.

---

## 📋 User Approval Needed (Before Implementation)

Please confirm these decisions before I proceed with Salesforce integration:

- [ ] **Integration API Choice:** Standard Data API v61.0 (recommended) vs Headless 360 MCP (beta, not ready yet)
- [ ] **OAuth Setup Method:** Scripted setup (recommended) vs Manual instructions
- [ ] **Sample Data:** Include 15 mock tickets for demo purposes (recommended)
- [ ] **Salesforce Org Type:** Dev (scratch) org required for testing. Production/Sandbox for real use.

---

## 📞 Contact & Handoff Notes

### What's Working

✅ Python scraper fetches emails from Gmail and outputs `tickets.json`  
✅ React frontend displays tickets in an aesthetic gallery  
✅ Shared utilities available in `shared-config/ticket_helpers.py`

### What's Needed

⏳ Create `salesforce-headless/` directory and implement:
- `salesforce_config.py`
- `setup_salesforce_oauth.py`
- `salesforce_headless.py`
- `tokens/` directory
- Update `.env.example` with Salesforce section

### Files in Scratchpad (for handoff reference)

| File | Purpose |
|------|---------|
| `SAFELY_NAME_THIS_FILE.md` | Detailed handoff document with architecture, decisions, and implementation plan |

---

## 🚀 Quick Start Guide

### For Next Agent (LM Studio)

1. **Review `SAFELY_NAME_THIS_FILE.md`** for detailed implementation plan
2. **Confirm decisions** (API choice, OAuth method, sample data)
3. **Create directory structure:**
   ```bash
   mkdir -p bookmyshow-ticket-gallery/salesforce-headless/tokens
   mkdir -p bookmyshow-ticket-gallery/salesforce-headless/fixtures
   ```
4. **Create files** in order:
   - `salesforce_config.py`
   - `setup_salesforce_oauth.py`
   - `salesforce_headless.py`
   - Update `.env.example`
5. **Test with sample data:**
   ```bash
   # Copy sample tickets to shared-config
   cp react-app/public/tickets.json shared-config/sample_tickets.json
   ```
   ```bash
   cd salesforce-headless
   python setup_salesforce_oauth.py
   # ... follow OAuth flow ...
   python salesforce_headless.py --input fixtures/sample_tickets.json
   ```

### For User (when demo is ready)

1. **Gmail OAuth Setup:**
   ```bash
   cd bookmyshow-ticket-gallery/python-scraper
   python setup_gmail_oauth.py
   # ... follow browser prompts ...
   ```

2. **Run Scraper:**
   ```bash
   python main_scraper.py
   # ... checks Gmail, parses emails, outputs tickets.json ...
   ```

3. **Salesforce OAuth Setup:**
   ```bash
   cd salesforce-headless
   python setup_salesforce_oauth.py
   # ... follow browser prompts ...
   ```

4. **Push to Salesforce:**
   ```bash
   cd salesforce-headless
   python salesforce_headless.py
   ```

---

## 📊 Project Progress Summary

| Component | Status | Files | Next Steps |
|-----------|--------|-------|------------|
| Python Scraper | ✅ Complete | 5 files | None |
| React Frontend | ✅ Complete | 9 files | None |
| Shared Config | ✅ Complete | 1 file | None |
| Salesforce Integration | ❌ Not Started | 0 files | **START HERE** |
| **Estimated Time:** | ~2 hours for Salesforce integration if ahead of schedule | | |

---

*This handoff document was created by the Bionic App agent. Review thoroughly before proceeding.*