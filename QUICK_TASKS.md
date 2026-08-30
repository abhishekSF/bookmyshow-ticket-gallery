# 🚀 Quick Task Checklist: Salesforce Headless Integration

**From: PROJECT_HANDOFF.md → PROJECT_STATUS.md**

## Current State
- ✅ Gmail API setup
- ✅ Email parsing + Ollama enrichment
- ✅ React gallery
- ❌ **Salesforce integration NOT STARTED**

## Immediate Tasks

### 1. Create Directory Structure
```bash
cd bookmyshow-ticket-gallery
mkdir -p salesforce-headless/tokens
mkdir -p salesforce-headless/fixtures
```

### 2. Create Salesforce Config
**File:** `salesforce-headless/salesforce_config.py`

```python
"""
Salesforce Headless 360 Connection Settings
Uses Standard Data API v61.0
"""
import os
from pydantic_settings import BaseSettings

class SalesforceSettings(BaseSettings):
    sf_url: str = "https://test-dev-ed.sfdc.us"
    sf_client_id: str = os.getenv("SF_CLIENT_ID", "")
    sf_client_secret: str = os.getenv("SF_CLIENT_SECRET", "")
    sf_refresh_token: str = os.getenv("SF_REFRESH_TOKEN", "")
    sf_tenant_id: str = os.getenv("SF_TENANT_ID", "")
    sf_enabled: bool = os.getenv("SF_ENABLE", "false").lower() == "true"
    sf_api_url: str = f"{sf_url}/services/data/v61.0"
    
    @property
    def is_ready(self) -> bool:
        return self.sf_enabled and bool(self.sf_client_id) and bool(self.sf_refresh_token)
    
    @property  
    def access_token(self) -> str:
        import base64, json
        token_data = json.load(open("tokens/token.json"))
        if "access_token" in token_data:
            token = token_data["access_token"]
            if token_data.get("expiry") and token_data["expiry"] < datetime.now().timestamp():
                # Refresh token
                from google.auth import refreshable
                creds = refreshable.Credentials(token)
                # ... refresh logic ...
            return token
        return ""
```

### 3. Update .env.example
```bash
# Salesforce Headless 360
SF_URL=https://test-dev-ed.sfdc.us
SF_CLIENT_ID=your-sfdc-connected-app-client-id
SF_CLIENT_SECRET=your-sfdc-connected-app-client-secret  
SF_REFRESH_TOKEN=your-sfdc-refresh-token
SF_TENANT_ID=your-sfdc-tenant-id
SF_ENABLE=false
```

### 4. Run OAuth Setup
```bash
cd salesforce-headless
python setup_salesforce_oauth.py
```

**Browser Flow:**
1. Authorize on `login.salesforce.com`
2. Get callback URL (copy from URL bar)
3. Paste callback URL back into script
4. Script saves `tokens/token.json`

### 5. Create Salesforce Custom Object

**Option A - sf CLI:**
```bash
sf object new Ticket__c -f object-meta.xml
```

**Option B - Setup UI:**
- Setup → Object Manager → New Custom Object
- API Name: `Ticket__c`  
- Label: `Ticket`
- Plurallabel: `Tickets`
- Fields:
  - `Event_Name__c` - Text (255)
  - `Venue__c` - Text (255)
  - `Show_Date__c` - DateTime
  - `Seats__c` - Text (255)
  - `Booking_Id__c` - Text (255, External ID)
  - `Amount__c` - Currency
  - `Poster_URL__c` - URL
  - `Category__c` - Picklist (Movie/Concert/Sports/Comedy/Play)
  - `Status__c` - Picklist (Created/Updated/Failed)

### 6. Create Sample Data
**File:** `salesforce-headless/fixtures/sample_tickets.json`
```json
{
  "tickets": [
    {
      "booking_id": "BM20250115-001",
      "event_name": "Dangal",
      "venue": "PVR Juhu", 
      "show_date": "15 January 2025",
      "show_time": "06:30 PM",
      "seats": "2A",
      "amount_paid": 1800,
      "poster_url": "https://image.tmdb.org/p/...",
      "category": "movie"
    },
    // ... 14 more tickets
  ]
}
```

### 7. Implement Main Integration
**File:** `salesforce-headless/salesforce_headless.py`

```python
"""
Salesforce Headless Integration
Batch inserts Ticket__c records via Data API v61.0
"""
from salesforce_config import settings
import json
import requests
from datetime import datetime

class SalesforceHeadless:
    def __init__(self):
        self.api_url = settings.sf_api_url
        self.access_token = settings.access_token
        
    def _transform_date(self, date_str: str, time_str: str = None) -> str:
        # Use shared helpers for date conversion
        from ...shared.ticket_helpers import format_show_datetime
        dt = format_show_datetime(date_str, time_str)
        # Convert to ISO 8601
        return f"{dt}Z"
    
    def _transform_currency(self, amount: str | int) -> dict:
        from ...shared.ticket_helpers import transform_currency
        return transform_currency(amount)
    
    def insert_batch(self, tickets: list) -> dict:
        records = []
        for t in tickets:
            record = {
                "sObjectType": "Ticket__c",
                "data": {
                    "Event_Name__c": t["event_name"],
                    "Venue__c": t["venue"],
                    "Show_Date__c": self._transform_date(t["show_date"], t.get("show_time")),
                    "Seats__c": t["seats"],
                    "Booking_Id__c": t["booking_id"],
                    "Amount__c": self._transform_currency(t["amount_paid"]),
                    "Poster_URL__c": t.get("poster_url", ""),
                    "Category__c": t["category"],
                    "Status__c": "Created"
                },
                "externalId": t["booking_id"]
            }
            records.append(record)
        
        payload = {
            "jobId": None,
            "records": records,
            "actionLabel": "Created"
        }
        
        response = requests.post(
            f"{self.api_url}/sobjects/Ticket__c/batch",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        
        return response.json()
```

### 8. Test & Run
```bash
# Test with sample data first
python salesforce_headless.py --input fixtures/sample_tickets.json

# Then push real tickets
python salesforce_headless.py --input react-app/public/tickets.json
```

### 9. Verify in Salesforce
```bash
# Check Dev Org
sf query Ticket__c --limit 50
```

---

## Quick Reference: Date & Currency Transformations

| Field | BookMyShow Format | Salesforce Format |
|-------|-------------------|-------------------|
| **Show_Date__c** | `"15 January 2025"` | `"2025-01-15T06:30:00.000Z"` |
| **Amount__c** | `1800` or `"₹1800"` | `{"value": 1800, "currencyCode": "INR"}` |

---

## After This Session

Once Salesforce integration works, you can:
1. Switch to LM Studio
2. Continue with:
   - Token auto-refresh
   - Error handling
   - Tableau dashboard
   - Production deployment

---

**Open PROJECT_STATUS.md for full context**