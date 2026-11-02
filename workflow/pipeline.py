"""Report Radar - Week 7 workflow pipeline (Role 4: Integration and Automation Lead).

Takes a brand-new citizen report through every stage of the workflow, so a
report goes from "a resident typed something" to "a team has it, with a
deadline, and the right people have been emailed" without anyone copying
data by hand.

This first part is the ticket store: every ticket is one row of
workflow/data/tickets.csv, in the column order the team agreed
(see workflow/README.md).
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "workflow" / "data"
TICKETS_FILE = DATA_DIR / "tickets.csv"

# The shared ticket, agreed by the team on day 1. Don't change the order.
COLUMNS = [
    "ticket_id", "received_at", "description_masked", "ward", "resident_contact",
    "category", "urgency", "review_required", "reason", "assigned_team", "depot",
    "sla_hours", "due_by", "status", "approval_status", "approver", "decision_note",
    "last_updated",
]


# ---------- ticket store ----------
def load_tickets(path: Path | None = None) -> list[dict]:
    """All saved tickets, oldest first. An empty list if there are none yet."""
    path = Path(path or TICKETS_FILE)
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def save_ticket(ticket: dict, path: Path | None = None) -> dict:
    """Add a new ticket, or replace the saved one with the same ticket_id.
    Only the agreed columns are written, so nothing extra (such as an email
    address) can slip into the file."""
    path = Path(path or TICKETS_FILE)
    tickets = load_tickets(path)
    row = {column: "" if ticket.get(column) is None else ticket.get(column) for column in COLUMNS}
    for index, saved in enumerate(tickets):
        if saved.get("ticket_id") == row["ticket_id"]:
            tickets[index] = row
            break
    else:
        tickets.append(row)
    _write_all(tickets, path)
    return row


def _write_all(tickets: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(tickets)
    temporary.replace(path)  # write then swap, so a crash never leaves half a file


def next_ticket_id(tickets: list[dict]) -> str:
    """TKT-000001, TKT-000002, ... one higher than the highest saved number."""
    numbers = [int(match.group(1)) for ticket in tickets
               if (match := re.fullmatch(r"TKT-(\d+)", str(ticket.get("ticket_id", ""))))]
    return f"TKT-{max(numbers, default=0) + 1:06d}"
