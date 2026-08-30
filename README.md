# Theatre gallery + Headless 360

Movie confirmation emails from one Gmail mailbox become `tickets.json`. The React gallery reads that file. The Salesforce adapter writes `Ticket__c` from that file. Nothing else is a source of truth.

Spec: [`plan.md`](plan.md).

## Layout

- `python-scraper/` — fetch, filter, parse, enrich, posters, export, dry-run, upsert
- `react-app/` — read-only gallery
- `shared-config/ticket_helpers.py` — record shape, IST dates, Salesforce payload
- `react-app/public/tickets.json` — the seam

## Setup

```bash
cp .env.example .env
# fill Gmail desktop OAuth client, optional TMDb, optional Salesforce Connected App
cd python-scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup_gmail_oauth.py          # gmail.readonly only
```

Ollama is optional and local (`llama3.1:8b` or `qwen2.5:7b-instruct`). Salesforce needs a Dev Org `Ticket__c` object with `Booking_Id__c` as an External ID, then `python setup_salesforce_oauth.py`.

## Fetch → parse → gallery

Stages run alone. Raw mail is stored under `python-scraper/data/raw_emails/<message-id>.json`.

```bash
cd python-scraper
python main_scraper.py fetch
python main_scraper.py filter
python main_scraper.py parse
python main_scraper.py enrich      # no-op if Ollama is down; never edits factual fields
python main_scraper.py posters     # TMDb by title; miss = fallback art
python main_scraper.py export      # tickets.json + review.json
```

Or `python main_scraper.py pipeline --fetch`.

Export writes `react-app/public/tickets.json` (complete and incomplete) and `python-scraper/data/review.json` (incomplete only).

```bash
cd react-app
npm install
npm run dev
```

Gallery: year / cinema / city filters, sort, dark-gradient film icon when `poster_url` is missing.

## Salesforce dry-run and confirm

The write adapter reads `tickets.json` only. It never reads Gmail.

```bash
cd python-scraper
python main_scraper.py dry-run
python main_scraper.py upsert              # prints dry-run, writes nothing
python main_scraper.py upsert --confirm    # complete records only
```

Dry-run layout:

```
Dry-run summary
---------------
Total tickets:      18
Complete:           16
Incomplete:          2
Would create:       14
Would update:        2
Would skip:          2
```

`--confirm` cannot push `complete: false`. Missing booking IDs are `BMS_MISSING_<source_message_id>` and stay incomplete. Headless 360 PATCH by `Booking_Id__c` runs first; REST sObject upsert is the fallback. There is no local sync file.

`Show_Date_Text__c` is always the raw string. `Show_Date__c` is set only when `show_date_iso` is a confident `+05:30` datetime. Year is never taken from Gmail received time.

## Tableau stretch

```bash
python main_scraper.py tableau
```

Writes `python-scraper/data/tableau.csv` without booking IDs, exact seats, or Gmail message IDs.

## Tests

```bash
cd python-scraper
pytest tests -q
```

The lock tests prove: ISO includes `+05:30`, a dateless year is not filled from Gmail received time, and `--confirm` refuses `complete: false`.

## Secrets

Stay in `.env` or gitignored `tokens/`. Gmail scope is readonly. Connected App: `Ticket__c` create and update. Ollama stays on localhost.
