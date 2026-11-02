"""Report Radar - Week 7 workflow pipeline (Role 4: Integration and Automation Lead).

Takes a brand-new citizen report through every stage of the workflow, so a
report goes from "a resident typed something" to "a team has it, with a
deadline, and the right people have been emailed" without anyone copying
data by hand.

Steps, in order (process_report):
  1. mask      hide names, phone and ID numbers, emails and house numbers
  2. classify  problem type and urgency (intake/classifier.py)
  3. route     team, depot and deadline           (Role 1, workflow/routing.py)
  4. approve   wait for a supervisor if urgent or unclear (Role 2, workflow/approvals.py)
  5. notify    email the resident, team or supervisor     (Role 3, workflow/notify.py)
  6. save      one row of workflow/data/tickets.csv, in the agreed columns
  7. log       one row of the decision log (governance/logs/decisions.csv)

Until a teammate's module exists, the matching stand-in in
workflow/fallbacks.py is used, and the decision log says so.

If a step fails, the ticket is still saved, sent to the supervisor's
approval queue with a note saying which step failed, and the supervisor is
emailed. A report is never silently lost.

The resident's email address is only handed to the email step. It is never
saved in the ticket, the CSV or the decision log.
"""
from __future__ import annotations

import csv
import importlib
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for folder in (ROOT, ROOT / "intake"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from classifier import process_report as classify  # noqa: E402
from governance.privacy import mask_personal_info  # noqa: E402
from workflow import fallbacks  # noqa: E402

try:  # the workflow works the same without the decision log
    from governance.logger import log_decision
except ImportError:
    log_decision = None

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


# ---------- choosing each step ----------
def step(module: str, name: str):
    """A teammate's real function if it exists, else the stand-in.
    Returns (function, is_stand_in)."""
    try:
        real = getattr(importlib.import_module(f"workflow.{module}"), name, None)
    except ImportError:
        real = None
    return (real, False) if callable(real) else (getattr(fallbacks, name), True)


def now_iso(now=None) -> str:
    when = now if isinstance(now, datetime) else (
        datetime.fromisoformat(now) if now else datetime.now().astimezone())
    return when.isoformat(timespec="seconds")


def _log(ticket_id: str, summary: str, output: str, reason: str) -> None:
    if log_decision is not None:
        log_decision("workflow", ticket_id, summary, output, reason)


# ---------- the whole flow for one report ----------
def process_report(text: str, ward: str, resident_email: str | None = None, now=None) -> dict:
    """Take one new report through every step and return the saved ticket."""
    when = now_iso(now)
    tickets = load_tickets()
    ticket = {column: "" for column in COLUMNS}
    ticket.update(ticket_id=next_ticket_id(tickets), received_at=when, ward=ward,
                  resident_contact="yes" if resident_email else "no",
                  status="new", last_updated=when)
    stand_ins, done = [], "mask"
    try:
        ticket["description_masked"] = mask_personal_info(str(text)).strip()
        done = "classify"
        result = classify(ticket["description_masked"])
        ticket.update(category=result["category"], urgency=result["urgency"],
                      review_required=result["review_required"], reason=result["reason"])
        done = "route"
        route, fake = step("routing", "route")
        stand_ins += ["routing"] if fake else []
        ticket = route(ticket)
        done = "approve"
        start, fake = step("approvals", "start")
        stand_ins += ["approvals"] if fake else []
        ticket = start(ticket, when)
        done = "save"
        save_ticket(ticket)
        done = "notify"
        notify, fake = step("notify", "notify")
        stand_ins += ["notify"] if fake else []
        if resident_email:
            notify("received", ticket, resident_email=resident_email, now=when)
        event = "approval_needed" if ticket.get("approval_status") == "pending" else "assigned"
        notify(event, ticket, now=when)
    except Exception as error:  # never lose a report: save it for a person to check
        return _park_failed(ticket, done, error, when)

    _log(ticket["ticket_id"], ticket["description_masked"],
         f"status={ticket['status']}; team={ticket['assigned_team']}; due_by={ticket['due_by']}",
         f"category={ticket['category']}, urgency={ticket['urgency']}"
         + (f"; stand-ins used: {', '.join(stand_ins)}" if stand_ins else ""))
    return ticket


def _park_failed(ticket: dict, stage: str, error: Exception, when: str) -> dict:
    """Save a ticket whose processing failed, in the supervisor's approval
    queue, with a note saying which step failed, and email the supervisor."""
    ticket = dict(ticket, status="awaiting_approval", approval_status="pending", last_updated=when,
                  decision_note=f"Automatic processing failed at the {stage} step; please check by hand.")
    if not ticket.get("assigned_team"):
        ticket["assigned_team"] = "Intake desk"
    if not ticket.get("description_masked"):
        ticket["description_masked"] = "(not shown: the report could not be masked)"
    save_ticket(ticket)
    _log(ticket["ticket_id"], ticket["description_masked"], "status=awaiting_approval (failed)",
         f"{stage} step failed: {type(error).__name__}")
    try:
        fallbacks.notify("approval_needed", ticket, now=when)
    except Exception:  # the ticket is saved and logged even if the email fails
        pass
    return ticket
