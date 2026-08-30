# 📊 Project Status: BookMyShow Ticket Gallery + Salesforce Headless 360

**Last Updated:** `(fill in current date)`  
**Current Phase:** Step 5 - Salesforce Headless Integration (NOT STARTED)

---

## 📁 Project Structure

```
bookmyshow-ticket-gallery/
├── python-scraper/              # ✅ COMPLETE
│   ├── config.py               # Settings management (pydantic)
│   ├── gmail_client.py         # Gmail API client + email parser
│   ├── main_scraper.py         # Main orchestration
│   ├── ollama_client.py        # LLM enrichment client
│   ├── scraper.py              # CLI entry point
│   └── requirements.txt        # Python dependencies
│
├── react-app/                  # ✅ COMPLETE
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   ├── index.js
│   ├── src/
│   │   ├── App.jsx             # Main app with routing
│   │   ├── components/
│   │   │   ├── Gallery.jsx     # Ticket gallery component
│   │   │   ├── Loading.jsx     # Loading state component
│   │   │   └── TicketCard.jsx  # Individual ticket card
│   │   └── utils/
│   │       └── ticketHelpers.js # Date/currency/category helpers
│   └── public/
│       └── tickets.json       # Output from scraper
│
├── shared-config/             # ✅ COMPLETE
│   └── ticket_helpers.py       # Shared utilities for Python
│
├── salesforce-headless/       # ⏳ TODO - NOT STARTED
│   ├── config.py              # Salesforce connection settings
│   ├── setup_salesforce_oauth.py # OAuth 2.0 setup script
│   ├── salesforce_headless.py # Main integration module
│   ├── tokens/                # OAuth token storage
│   └── fixtures/              # Sample data for testing
│
├── .env.example               # ⏳ NEEDS UPDATE - Add Salesforce section
└── PROJECT_STATUS.md          # 📄 This file
```

---

## ✅ Completed Work

### 1. Python Scraper (`python-scraper/`)

#### **config.py** - Configuration Management
- Settings loaded from `.env` via `pydantic_settings`
- Services tracked: Gmail, Ollama, TMDb, Salesforce
- Gmail OAuth token cached locally in `tokens/token.json`
- **Key config**:
  - `gmail_enabled`, `gmail_client_id`, `gmail_client_secret`
  - `ollama_enable`, `ollama_model` (llama3.1:8b or qwen2.5:7b-instruct)
  - `tmdb_enable`, `tmdb_api_key`
  - `sf_enabled`, `sf_client_id`, `sf_refresh_token` (NOT SETUP YET)

#### **gmail_client.py** - Gmail API + Email Parsing
- Uses `google-api-python-client` for Gmail API
- OAuth 2.0 flow with `google-auth` and `google-auth-oauthlib`
- **Search query**: `from:noreply@bookmyshow.com OR from:bookmyshow`
- Uses `beautifulsoup4` for HTML parsing
- **Extracts per email**:
  - `event_name`, `venue`, `show_date`, `show_time`
  - `seats`, `booking_id`, `amount_paid`
  - `poster_url` (if present in HTML)
  - `category` (inferred)
- **Confidence scoring**: Based on field extraction completeness
- **Fallback**: Low-confidence extractions routed to Ollama

#### **main_scraper.py** - Main Orchestration
- Fetches emails from Gmail
- Parses with deterministic parser (BS4 + regex)
- Routes low-confidence (<70%) to Ollama for enrichment
- Ollama used for:
  - Cleaning inconsistent venue names
  - Inferring genre/category
  - Writing one-line event blurb
  - Resolving ambiguous cases
- **Poster fallback**: TMDb API lookup for movies (no coverage for concerts/sports/comedy)
- Outputs `tickets.json` with structured records

#### **ticket_helpers.py** (in `shared-config/`) - Shared Utilities
- `clean_text()` - Remove extra whitespace, special chars
- `normalize_venue_name()` - Remove location/class suffixes
- `infer_category()` - Map category hints to standard categories
- `validate_date()` - Parse Indian date formats to ISO
- `format_show_datetime()` - Combine date + time
- `get_category_color()` - Tailwind color classes per category
- `get_category_icon()` - Emoji/icon per category

### 2. React Frontend (`react-app/`)

#### **Tech Stack**
- Vite + React + Tailwind CSS
- Local dev server (port 5173)
- **No backend needed** for v1 (reads static `tickets.json`)

#### **Components**
- **Gallery.jsx** - Grid of ticket cards with filters/sort
- **Loading.jsx** - Skeleton loading states
- **TicketCard.jsx** - Individual ticket card design:
  - Poster image
  - Event name
  - Venue, date, time
  - Seat info
  - Category badge
  - Amount

#### **Utils (`ticketHelpers.js`)**
- `CATEGORY_COLORS` - Tailwind colors per category
- `formatDate()` - Convert various formats to display string
- `formatCurrency()` - INR formatting with ₹ symbol
- `formatSeats()` - Display seat info
- `validateTicket()` - Validate ticket data structure
- `sortTicketsByDate/Amount()` - Sorting functions
- `aggregateByCategory()` - Category statistics

### 3. Shared Config (`shared-config/`)

#### **ticket_helpers.py**
- Date transformation: `"15 January 2025"` → ISO 8601
- Currency transformation: `1800` → `{"value": 1800, "currencyCode": "INR"}`
- Category inference and color mapping
- Grouping/aggregation utilities

---

## ⏳ Not Started / Needs Work

### **Phase 1: Salesforce Integration (Step 5 from original plan)**

#### **Directory Structure to Create**
```bash
mkdir -p bookmyshow-ticket-gallery/salesforce-headless/tokens
mkdir -p bookmyshow-ticket-gallery/salesforce-headless/fixtures
```

#### **Files to Create**

1. **`salesforce_config.py`** - Connection settings
   - Load from `.env`
   - Store OAuth tokens in `tokens/token.json`
   - Base URL: `https://test-dev-ed.sfdc.us/services/data/v61.0`
   - Target object: `Ticket__c`
   
2. **`setup_salesforce_oauth.py`** - OAuth 2.0 setup script
   - Create Connected App in Salesforce
   - Scripted OAuth flow (not manual copy-paste)
   - Save refresh token to `tokens/token.json`
   - Token refresh logic (access tokens expire)
   
3. **`salesforce_headless.py`** - Main integration module
   - Authenticate using OAuth 2.0
   - Build batch API request to `/services/data/v61.0/sobjects/Ticket__c/batch`
   - Transform date (Indian → ISO 8601)
   - Transform currency (plain → `{"value": X, "currencyCode": "INR"}`)
   - Push records in batches of 50 (Salesforce limit)
   - Output job status and record IDs
   - Handle errors and retries

4. **`fixtures/sample_tickets.json`** - Sample data for testing
   - Include 15 mock tickets with varied categories
   - Mix of valid and edge-case dates/times
   - Simulate what the scraper would output

5. **Update `.env.example`**
   - Add Salesforce credentials section
   - Add instructions for Salesforce Connected App setup

---

## 🎯 Decisions Made

| Decision | Choice | Reason |
|----------|--------|--------|
| **Integration API** | Standard Data API v61.0 | Headless 360 MCP beta docs not ready; v61.0 is stable |
| **OAuth Method** | Scripted setup | Preferred over manual instructions for demo |
| **Sample Data** | 15 mock tickets | Allows testing without real Salesforce access |
| **Date Format** | Indian → ISO 8601 | Salesforce requires ISO datetime |
| **Currency Format** | Plain → Salesforce object | `{"value": X, "currencyCode": "INR"}` |
| **Backend** | None for v1 | Ollama called offline; React reads static JSON |

---

## 📋 Custom Object: `Ticket__c`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Event_Name__c` | Text (255) | Yes | Event/movie name |
| `Venue__c` | Text (255) | Yes | Venue name |
| `Show_Date__c` | DateTime | Yes | Show date and time (ISO 8601) |
| `Seats__c` | Text (255) | Yes | Seat information |
| `Booking_Id__c` | Text (255) | Yes | Booking ID (set as External ID) |
| `Amount__c` | Currency | Yes | Amount paid |
| `Poster_URL__c` | URL | No | Poster image URL |
| `Category__c` | Picklist | Yes | movie/concert/sports/comedy/play |
| `Status__c` | Picklist | No | Created/Updated/Failed |

---

## 🚀 Immediate Next Steps

### **Step 1: Create Directory Structure**
```bash
cd bookmyshow-ticket-gallery
mkdir -p salesforce-headless/tokens
mkdir -p salesforce-headless/fixtures
```

### **Step 2: Create Config Files**

**`salesforce_config.py`**
```python
"""
Salesforce Headless 360 Connection Settings
Uses Standard Data API v61.0
"""
```

**`setup_salesforce_oauth.py`**
```python
"""
Scripted Salesforce OAuth 2.0 Setup
1. Creates Connected App
2. Completes OAuth flow
3. Saves refresh token
"""
```

**`salesforce_headless.py`**
```python
"""
Salesforce Integration Module
- Authenticate with OAuth
- Batch insert Ticket__c records
- Date/currency transformation
- Error handling
"""
```

### **Step 3: Update `.env.example`**
```bash
# Salesforce Headless 360
SF_URL=https://test-dev-ed.sfdc.us
SF_CLIENT_ID=your-connected-app-client-id
SF_CLIENT_SECRET=your-connected-app-client-secret
SF_REFRESH_TOKEN=your-refresh-token
SF_TENANT_ID=your-tenant-id (Consumer Key)
SF_ENABLE=false
```

### **Step 4: Create Sample Data**
```json
{
  "tickets": [
    {
      "booking_id": "BM20250115-001",
      "event_name": "Dangal",
      "venue": "PVR Juhu",
      "show_date": "15 January 2025",
      "show_time": "06:30 PM",
      "seats": "2A, 2B",
      "amount_paid": 1800,
      "poster_url": "https://image.tmdb.org/...",
      "category": "movie",
      "confidence_score": 95
    }
  ]
}
```

### **Step 5: Run OAuth Setup**
```bash
cd salesforce-headless
python setup_salesforce_oauth.py
# Complete browser authorization flow
# Copy/paste refresh token back into script
# Token saved to tokens/token.json
```

### **Step 6: Create Salesforce Custom Object**
```bash
# Option 1: sf CLI
sf object new Ticket__c -f object-meta.xml

# Option 2: Setup UI
# Go to Setup → Object Manager → New Custom Object
# Fill in field configurations
```

### **Step 7: Test Integration**
```bash
cd salesforce-headless
python salesforce_headless.py --input ../shared-config/fixtures/sample_tickets.json
```

### **Step 8: Push Real Tickets (Optional)**
```bash
python salesforce_headless.py --input ../react-app/public/tickets.json
```

---

## 🐛 Known Issues / Caveats

| Priority | Issue | Mitigation |
|----------|-------|------------|
| **HIGH** | Gmail OAuth setup | Budget 5-10 minutes; follow script instructions |
| **HIGH** | Salesforce Custom Object | Must exist BEFORE running integration |
| **HIGH** | Salesforce OAuth Setup | Requires Connected App (5-10 min setup) |
| **MEDIUM** | Date format conversion | Indian format → ISO 8601 must be precise |
| **MEDIUM** | Email HTML variation | Parser needs per-template branches |
| **MEDIUM** | Token refresh | Access tokens expire; need periodic refresh |
| **LOW** | Batch size limit | Max 50 records per API batch |

---

## 🔧 Date Transformation (Indian → Salesforce ISO)

**Input Formats (BookMyShow emails):**
- `"15 January 2025, 06:30 PM"`
- `"25 December 2024, 08:00 PM"`
- `"2024-12-25 20:00:00"`

**Salesforce Expected Format (ISO 8601):**
- `"2025-01-15T18:30:00.000Z"`

**Transformation:**
```python
# Python helper (shared-config/ticket_helpers.py)
def format_show_datetime(date: str, time: str) -> str:
    """Convert Indian date format to ISO 8601"""
    # Parse date (DD/MM/YYYY or MonthName YYYY)
    # Parse time (HH:MM AM/PM or HH:MM)
    # Return ISO format: YYYY-MM-DDTHH:MM:SS.000Z
```

**Example:**
```python
format_show_datetime("15 January 2025", "06:30 PM")
# Returns: "2025-01-15T18:30:00.000Z"
```

---

## 💱 Currency Transformation

**Input (BookMyShow emails):**
- `1800` (plain number)
- `"₹1800"`
- `"INR 1800"`

**Salesforce Expected Format:**
```json
{
  "value": 1800,
  "currencyCode": "INR"
}
```

**Transformation:**
```python
# Python helper
def transform_currency(amount: str | int) -> dict:
    return {
        "value": float(amount) if isinstance(amount, str) else amount,
        "currencyCode": "INR"
    }
```

---

## 📡 Salesforce Data API Request Format

**Endpoint:** `POST /services/data/v61.0/sobjects/Ticket__c/batch`

**Request Body:**
```json
{
  "jobId": null,
  "records": [{
    "sObjectType": "Ticket__c",
    "data": {
      "Event_Name__c": "Dangal",
      "Venue__c": "PVR Juhu",
      "Show_Date__c": "2025-01-15T18:30:00.000Z",
      "Seats__c": "2A, 2B",
      "Booking_Id__c": "BM20250115-001",
      "Amount__c": {"value": 1800, "currencyCode": "INR"},
      "Poster_URL__c": "https://image.tmdb.org/...",
      "Category__c": "Movie",
      "Status__c": "Created"
    },
    "externalId": "BM20250115-001"
  }],
  "actionLabel": "Created"
}
```

**Response Example:**
```json
{
  "success": {
    "total": 1,
    "failed": 0,
    "jobs": []
  },
  "errors": [],
  "done": true
}
```

---

## 🛠️ Environment Variables

**`.env.example` needs to be updated with:**

```bash
# Gmail API (Required for email fetching)
GMAIL_PROJECT_ID=your-google-cloud-project-id
GMAIL_CLIENT_ID=your-oauth-client-id
GMAIL_CLIENT_SECRET=your-oauth-client-secret

# Ollama (Optional for enrichment)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_ENABLE=false

# TMDb API (Optional for poster fallback)
TMDB_API_KEY=your-tmdb-api-key
TMDB_ENABLE=true

# Salesforce Headless 360 (To be added - REQUIRED for Step 5)
SF_URL=https://test-dev-ed.sfdc.us
SF_CLIENT_ID=your-sfdc-connected-app-client-id
SF_CLIENT_SECRET=your-sfdc-connected-app-client-secret
SF_REFRESH_TOKEN=your-sfdc-refresh-token
SF_TENANT_ID=your-sfdc-tenant-id
SF_ENABLE=false
```

---

## 📦 Dependencies to Install

### **Python**
```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
pip install pydantic pydantic-settings
pip install beautifulsoup4 requests
pip install click
```

### **Node.js**
```bash
# react-app already has package.json
npm install  # Install dependencies
```

---

## 🧪 Testing Strategy

### **Phase 1: Unit Tests**
- Test date transformation: Indian → ISO 8601
- Test currency transformation: Plain → Salesforce format
- Test category inference: Input hint → Standard category

### **Phase 2: Integration Tests**
- Test with sample fixture data (`sample_tickets.json`)
- Verify OAuth setup works
- Test batch insertion (50 record limit)
- Verify error handling for invalid records

### **Phase 3: End-to-End Test**
- Run full scraper to generate `tickets.json`
- Run Salesforce integration with real data
- Verify records appear in Salesforce Dev Org
- Check record IDs in response

---

## 📸 Screenshots / Demo Checklist

- [ ] Gmail OAuth consent screen
- [ ] Scraper console output
- [ ] OAuth consent for Salesforce
- [ ] React gallery running
- [ ] Salesforce records in Dev Org (query: `Ticket__c`)
- [ ] Optional: Tableau dashboard

---

## 🚧 Roadmap

### **Completed**
- [x] Gmail OAuth setup
- [x] Email parsing (deterministic)
- [x] Ollama enrichment
- [x] TMDb poster lookup
- [x] tickets.json generation
- [x] React gallery UI
- [x] Shared utilities

### **In Progress**
- [ ] Salesforce OAuth setup
- [ ] Salesforce Custom Object `Ticket__c`
- [ ] Salesforce Data API integration
- [ ] Date/currency transformation
- [ ] Batch record insertion

### **Future (v2)**
- [ ] Live FastAPI backend (for v2 - live Ollama/Salesforce calls)
- [ ] Tableau Public dashboard
- [ ] Token auto-refresh logic
- [ ] Error monitoring/notifications

---

## 📞 Getting Help

**Gmail OAuth Issues?**
- Check API enabled in Google Cloud Console
- Verify `credentials.json` exists
- Check `tokens/token.json` is created

**Salesforce OAuth Issues?**
- Verify Connected App created
- Check Callback URL matches script
- Verify refresh token is properly saved

**API Errors?**
- Check `Ticket__c` object exists
- Verify field names match exactly (case-sensitive!)
- Check API version compatibility (v61.0)

---

## 📚 Key Files Reference

| File | Path | Purpose |
|------|------|---------|
| `ticket_helpers.py` | `shared-config/ticket_helpers.py` | Date/currency helpers |
| `main_scraper.py` | `python-scraper/main_scraper.py` | Main scraper entry |
| `App.jsx` | `react-app/src/App.jsx` | React gallery UI |
| `salesforce_headless.py` | `salesforce-headless/salesforce_headless.py` | Salesforce integration (TODO) |
| `setup_salesforce_oauth.py` | `salesforce-headless/setup_salesforce_oauth.py` | Salesforce OAuth (TODO) |
| `salesforce_config.py` | `salesforce-headless/salesforce_config.py` | Salesforce config (TODO) |
| `tokens/token.json` | `salesforce-headless/tokens/token.json` | OAuth tokens (TODO) |
| `.env` | `./` | Environment variables |
| `.env.example` | `./` | Environment template (NEEDS UPDATE) |

---

## 🎯 Summary: Where We Are

| Component | Status | Notes |
|-----------|--------|-------|
| **Gmail API** | ✅ Ready | OAuth configured, can fetch emails |
| **Email Parser** | ✅ Complete | Deterministic extraction working |
| **Ollama Enrichment** | ✅ Complete | Local LLM for cleanup only |
| **TMDb Poster** | ✅ Ready | Fallback for movies |
| **tickets.json** | ✅ Generated | Local structured dataset |
| **React Frontend** | ✅ Complete | Gallery UI working |
| **Shared Helpers** | ✅ Complete | Date/currency transforms |
| **Salesforce Integration** | ⏳ NOT STARTED | Main focus for next work session |

---

## ⏭️ Next Session Tasks

1. Create `salesforce-headless/` directory structure
2. Write `salesforce_config.py` (connection settings)
3. Write `setup_salesforce_oauth.py` (OAuth 2.0 setup script)
4. Create `fixtures/sample_tickets.json` (15 mock tickets)
5. Update `.env.example` with Salesforce section
6. Create Salesforce Custom Object `Ticket__c`
7. Implement `salesforce_headless.py` (batch insert)
8. Test with sample data
9. Push real tickets (optional)

---

**End of Project Status**