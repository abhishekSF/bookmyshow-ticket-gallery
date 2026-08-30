"""Optional Tableau CSV: strip booking IDs, exact seats, and Gmail message IDs."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from config import TABLEAU_CSV_PATH, settings

SHARED = Path(__file__).resolve().parent.parent / "shared-config"
sys.path.insert(0, str(SHARED))

from ticket_helpers import strip_for_tableau  # noqa: E402

PRIVATE_COLUMNS = {"booking_id", "seats", "seat_display", "source_message_id"}
COLUMNS = (
    "movie_title",
    "cinema_name",
    "city",
    "year",
    "month",
    "quantity",
    "amount",
    "currency",
    "poster_url",
)


def export_csv(
    tickets_path: Path,
    output_path: Path = TABLEAU_CSV_PATH,
) -> Path:
    data = json.loads(Path(tickets_path).read_text())
    tickets: List[Dict[str, Any]] = data["tickets"] if isinstance(data, dict) else data
    rows = strip_for_tableau(tickets)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            assert PRIVATE_COLUMNS.isdisjoint(row.keys())
            writer.writerow(row)
    return output_path
