# Theatre gallery + Headless 360

Sunday 30 Aug 2026. One mailbox. Movie bookings only. Headless 360 writes Ticket__c in a Salesforce Dev Org.

## Why this exists

Abhishek is building a personal theatre-movie gallery from BookMyShow confirmation emails in Gmail. The gallery is a keepsake. Salesforce is the system of record. Sunday runs local extract, local enrichment, posters, and a Headless 360 upsert. No Lightning data entry. No product.

This is an art-of-possible demo on a real mailbox. Concerts, sports, comedy, and live theatre are scored and skipped, not parsed. Done means one complete ticket on disk, one gallery card, and one Ticket__c row written by code.

## Architecture

Nine named stages, one file seam. tickets.json is the contract between parse, gallery, and Salesforce write. The gallery only reads that file. The write adapter only reads that file.

Headless 360 and standard REST sit behind one upsert interface keyed on Booking_Id__c. Swap the adapter, keep the payload. The v1 store is the JSON file. The durable thing is the record shape. No Kubernetes, queues, multi-tenant IAM, event buses, or SQL database.

## Stage contracts

1. Gmail fetch. Readonly OAuth. Raw emails on disk by message id. BookMyShow senders, booking, confirmation, or ticket subjects.
2. Movie-vs-event filter. Movie markers: Cinema, Screen, IMAX, PVR, INOX, Cinepolis. Event markers: Concert, Match, Comedy, Theatre, Festival. Skip if event score wins. One keyword is not a decision.
3. Deterministic parse. Booking ID, movie title, cinema, date and time, seats, amount, currency. Sets complete and missing_fields. No Ollama.
4. Ollama enrichment. Cinema name, city, blurb only. llama3.1:8b or qwen2.5:7b-instruct, temperature 0, strict JSON, validate then merge. Discard on failure. Ollama does not touch factual fields. Period.
5. TMDb posters. Lookup by title. Miss: dark gradient plus film icon.
6. Export to tickets.json. Incomplete also in review.json.
7. Salesforce dry-run. Payload plus create, update, skip counts. No write.
8. Salesforce upsert. Complete records, --confirm only. Headless 360 PATCH by Booking_Id__c. REST fallback. No local sync file.
9. Optional Tableau from a stripped CSV: movies per year or month, spend, top cinemas.

## Record contract

tickets.json fields: booking_id, movie_title, cinema_raw, cinema_name, city, show_date_raw, show_date_iso, seats[], seat_display, quantity, amount, currency, poster_url, poster_source, blurb, source_message_id, complete, missing_fields[].

Example. booking_id BMS123456789. movie_title Dune: Part Two. cinema_raw "PVR Forum Mall, Koramangala, Bengaluru". cinema_name "PVR Forum Mall". city Bengaluru. show_date_raw "Sat, 15 Mar, 7:30 PM". show_date_iso "2026-03-15T19:30:00+05:30". seats ["G12", "G13"]. amount 980. currency INR. poster_source tmdb. complete true.

When set, show_date_iso must include +05:30. Dropping the offset is a bug. Date, time, and a clearly Indian venue or city convert to ISO 8601 with +05:30. Missing year or any other partial date: show_date_raw only, show_date_iso null. Do not infer year from Gmail received time. Salesforce always gets Show_Date_Text__c. Leave Show_Date__c empty rather than guess.

Missing booking ID becomes BMS_MISSING_<source_message_id>, complete false. Complete means booking_id, movie_title, and show_date_raw. Seats, amount, and currency may be absent. Incomplete stays in tickets.json and review.json. --confirm does not override complete: false. Category is always Movie.

## Salesforce object

Ticket__c: Event_Name__c Text, movie title. Venue__c Text, cinema name. Venue_City__c Text. Show_Date__c DateTime, only when confidently parsed. Show_Date_Text__c Text, always the raw string. Seats__c Text, comma-separated. Quantity__c Number. Booking_Id__c Text, unique External ID, upsert key. Amount__c Currency. Currency__c Text. Poster_URL__c URL. Source_Message_Id__c Text. Category__c Text, always Movie.

Write set is complete: true only.

## Write-gate contract

Dry-run before every real push. No --confirm, no write. Print this layout.

```
Dry-run summary
---------------
Total tickets:      18
Complete:           16
Incomplete:          2
Would create:       14
Would update:        2
Would skip:          2

Sample payload: { Event_Name__c, Venue__c, Show_Date__c, Show_Date_Text__c, Seats__c, Booking_Id__c, Amount__c, Currency__c, Category__c }
```

Would skip is incomplete records plus adapter refusals. Counts must match tickets.json before --confirm.

## Security

Gmail scope is gmail.readonly. Never request modify or send. Secrets live in env or gitignored files: OAuth client, tokens.json, TMDb key, Connected App credentials. Ollama stays local. Booking text does not leave the machine for enrichment. Connected App: Ticket__c create and update, describe if needed. No unrelated objects. Private: booking IDs, exact seats, Gmail message IDs. Publishable after strip: posters, titles, cinema, city, month, spend totals. Tableau Public is public. Strip before upload.

## Reliability

Fail closed. Incomplete never upserts. Ollama failure discards enrichment and keeps deterministic fields. TMDb miss uses fallback art. Re-run is safe via Booking_Id__c upsert. Raw emails stay on disk so a parser rewrite does not need another Gmail fetch. review.json is quarantine.

## Scale

One mailbox, tens to hundreds of tickets. tickets.json is the right store. No database, queue, or second-user model in v1. At 10k tickets or a second mailbox, swap the file for a store, keep the record contract, keep the write adapter.

## Composability

Stages run alone: fetch, filter, parse, enrich, posters, export, dry-run, upsert. Gallery never writes. Salesforce write never reads Gmail. Tableau never sees Salesforce live.

Free stack: Gmail API, BeautifulSoup, dateutil, Ollama, TMDb, Vite, Tailwind, Salesforce Dev Org, Tableau Public via CSV.

## Sunday time-box

30 Aug 2026, Asia/Calcutta.

- 08:30-09:00 Pre-flight: Gmail, Ollama, Dev Org, Ticket__c External ID, Vite.
- 09:00-09:45 Gmail OAuth and fetch.
- 09:45-11:15 Movie-only parser to tickets.json.
- 11:15-12:00 Ollama enrichment and TMDb posters.
- 12:00-13:00 Lunch.
- 13:00-14:30 React gallery: stub cards, year/cinema/city filters, sort.
- 14:30-16:00 Salesforce dry-run, upsert, verify. REST fallback. Auth is the sink.
- 16:00-16:30 Stretch only if ahead: CSV to Tableau Public.
- 16:30 onward. README, screenshots, demo script.

## Success

- One real BookMyShow movie email parsed into a complete ticket.
- tickets.json on disk. Gallery renders it with a poster or fallback.
- Dry-run prints the counts layout above.
- One confirmed upsert visible on Ticket__c, or REST fallback did the same.
- Demo walked in under 5 minutes on the narrative below.

Tableau Public is stretch. The day is done without it.

## Out of scope for v1

Non-movie bookings, live backend, frontend-triggered Ollama, live Salesforce push from React, Tableau live Salesforce connection, SQL database, multi-user support, refund, cancellation, reschedule, broad event-category classification.

## Demo narrative

Gmail is the source system. A local Python pipeline extracts movie-ticket data. Ollama enriches messy text locally and never touches factual fields. TMDb supplies poster art. React is the personal experience layer. Salesforce is the system of record, written through Headless 360. Tableau Public optionally visualizes a stripped CSV.

## Risks

Gmail OAuth is the early time sink.

Headless 360 tooling is new as of TDX 2026. Verify whether MCP write tools use standard Connected App OAuth or something MCP-specific. Keep the REST fallback ready.

Tableau Public data is public once uploaded. Strip booking IDs, exact seats, and message IDs, or do not publish.

## Tracking-bot handoff

Other bot name TBD. All statuses start as not-started: preflight, fetch, parse, enrich, gallery, salesforce-dry-run, salesforce-upsert, stretch-tableau, demo-pack. Track done, blocked, or skipped.

## Flow

flowchart LR: Gmail --> Filter --> Parse --> Enrich --> Posters; Posters --> Gallery; Posters --> DryRun --> Upsert --> TicketC; TicketC -.-> Tableau

## Later, only if it earns it

1. Refund, cancel, and reschedule handling.
2. Non-movie BookMyShow events as a second category.
3. A real store once tickets.json is actually painful.
4. Live Tableau against a private extract, never Public with unstripped IDs.
