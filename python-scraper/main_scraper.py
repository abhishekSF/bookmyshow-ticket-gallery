"""
CLI for the nine stages. Each subcommand is runnable alone.

  fetch | filter | parse | enrich | posters | export | dry-run | upsert | tableau
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from config import (
    ENRICHED_PATH,
    FILTERED_PATH,
    PARSED_PATH,
    POSTERS_PATH,
    RAW_EMAIL_DIR,
    ensure_data_dirs,
    settings,
)
from gmail_client import email_text, fetch_and_store, load_raw_emails
from movie_filter import is_movie_booking, score_email
from ollama_client import OllamaClient
from posters import apply_poster
from salesforce_write import dry_run, upsert_tickets
from scraper import parse_email
from tableau_export import export_csv

SHARED = Path(__file__).resolve().parent.parent / "shared-config"
sys.path.insert(0, str(SHARED))

from ticket_helpers import finalize_ticket, merge_ollama_enrichment  # noqa: E402


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {path}")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def cmd_fetch(args: argparse.Namespace) -> None:
    ensure_data_dirs()
    paths = fetch_and_store(max_results=args.max)
    print(f"Saved {len(paths)} raw email(s) under {RAW_EMAIL_DIR}")


def cmd_filter(args: argparse.Namespace) -> None:
    emails = load_raw_emails()
    kept: List[Dict[str, Any]] = []
    skipped = 0
    for email in emails:
        text = email_text(email)
        scores = score_email(text)
        if is_movie_booking(text):
            kept.append(
                {
                    "id": email.get("id"),
                    "scores": scores,
                    "subject": (email.get("headers") or {}).get("subject"),
                }
            )
        else:
            skipped += 1
            print(f"Skip event {email.get('id')}: {scores}")
    _write_json(FILTERED_PATH, kept)
    print(f"Kept {len(kept)} movie email(s); skipped {skipped}")


def _filtered_ids() -> set[str] | None:
    if not FILTERED_PATH.exists():
        return None
    rows = _read_json(FILTERED_PATH)
    return {row["id"] for row in rows if row.get("id")}


def cmd_parse(args: argparse.Namespace) -> None:
    emails = load_raw_emails()
    allowed = _filtered_ids()
    tickets = []
    for email in emails:
        if allowed is not None and email.get("id") not in allowed:
            continue
        text = email_text(email)
        if allowed is None and not is_movie_booking(text):
            continue
        tickets.append(parse_email(email))
    _write_json(PARSED_PATH, tickets)
    complete = sum(1 for t in tickets if t.get("complete"))
    print(f"Parsed {len(tickets)} ticket(s); complete={complete}")


def _latest_tickets() -> List[Dict[str, Any]]:
    for path in (POSTERS_PATH, ENRICHED_PATH, PARSED_PATH):
        if path.exists():
            return _read_json(path)
    raise SystemExit("No parsed tickets yet. Run: python main_scraper.py parse")


def cmd_enrich(args: argparse.Namespace) -> None:
    tickets = _read_json(PARSED_PATH) if PARSED_PATH.exists() else _latest_tickets()
    client = OllamaClient()
    if not client.available():
        print("Ollama unavailable; copying parsed tickets without enrichment.")
        _write_json(ENRICHED_PATH, tickets)
        return
    enriched = []
    for ticket in tickets:
        extra = client.enrich(ticket)
        if extra:
            ticket = merge_ollama_enrichment(ticket, extra)
            ticket = finalize_ticket(ticket)
        enriched.append(ticket)
    _write_json(ENRICHED_PATH, enriched)


def cmd_posters(args: argparse.Namespace) -> None:
    tickets = _read_json(ENRICHED_PATH) if ENRICHED_PATH.exists() else _latest_tickets()
    updated = [apply_poster(dict(ticket)) for ticket in tickets]
    _write_json(POSTERS_PATH, updated)


def cmd_export(args: argparse.Namespace) -> None:
    tickets = _latest_tickets()
    tickets = [finalize_ticket(dict(t)) for t in tickets]
    tickets_path = Path(args.tickets) if args.tickets else settings.tickets_path
    review_path = Path(args.review) if args.review else settings.review_path
    _write_json(tickets_path, tickets)
    incomplete = [t for t in tickets if not t.get("complete")]
    _write_json(review_path, incomplete)
    print(
        f"Export complete={sum(1 for t in tickets if t.get('complete'))} "
        f"incomplete={len(incomplete)}"
    )


def cmd_dry_run(args: argparse.Namespace) -> None:
    tickets_path = Path(args.tickets) if args.tickets else settings.tickets_path
    adapter = None
    if getattr(args, "lookup", False):
        from salesforce_write import build_adapter

        adapter = build_adapter()
    dry_run(tickets_path, adapter=adapter)


def cmd_upsert(args: argparse.Namespace) -> None:
    tickets_path = Path(args.tickets) if args.tickets else settings.tickets_path
    upsert_tickets(tickets_path, confirm=args.confirm)


def cmd_tableau(args: argparse.Namespace) -> None:
    tickets_path = Path(args.tickets) if args.tickets else settings.tickets_path
    path = export_csv(tickets_path)
    print(f"Wrote stripped CSV {path}")


def cmd_pipeline(args: argparse.Namespace) -> None:
    if args.fetch:
        cmd_fetch(args)
        cmd_filter(args)
    cmd_parse(args)
    cmd_enrich(args)
    cmd_posters(args)
    cmd_export(args)
    cmd_dry_run(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BookMyShow movie tickets: Gmail → tickets.json → gallery / Salesforce"
    )
    parser.add_argument("--tickets", help="Path to tickets.json")
    parser.add_argument("--review", help="Path to review.json")
    parser.add_argument("--max", type=int, default=50, help="Gmail max results")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fetch", help="Gmail readonly fetch; save raw mail by id")
    sub.add_parser("filter", help="Keep movie emails; skip if event score wins")
    sub.add_parser("parse", help="Deterministic parse to the tickets.json shape")
    sub.add_parser("enrich", help="Ollama cinema_name/city/blurb only")
    sub.add_parser("posters", help="TMDb poster lookup")
    exp = sub.add_parser("export", help="Write tickets.json and review.json")
    exp.add_argument("--tickets", help="Path to tickets.json")
    exp.add_argument("--review", help="Path to review.json")
    dry = sub.add_parser("dry-run", help="Salesforce dry-run; no write")
    dry.add_argument("--tickets", help="Path to tickets.json")
    dry.add_argument(
        "--lookup",
        action="store_true",
        help="Query Salesforce for existing Booking_Id__c values",
    )
    up = sub.add_parser("upsert", help="Upsert complete Ticket__c rows")
    up.add_argument("--tickets", help="Path to tickets.json")
    up.add_argument(
        "--confirm",
        action="store_true",
        help="Required to write. Incomplete records are never pushed.",
    )
    tab = sub.add_parser("tableau", help="Stripped CSV: no booking IDs, seats, or message IDs")
    tab.add_argument("--tickets", help="Path to tickets.json")
    pipe = sub.add_parser("pipeline", help="parse→enrich→posters→export→dry-run")
    pipe.add_argument("--fetch", action="store_true", help="Fetch Gmail before parse")
    pipe.add_argument("--tickets", help="Path to tickets.json")
    pipe.add_argument("--review", help="Path to review.json")
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    commands = {
        "fetch": cmd_fetch,
        "filter": cmd_filter,
        "parse": cmd_parse,
        "enrich": cmd_enrich,
        "posters": cmd_posters,
        "export": cmd_export,
        "dry-run": cmd_dry_run,
        "upsert": cmd_upsert,
        "tableau": cmd_tableau,
        "pipeline": cmd_pipeline,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
