"""TEMPORARY stand-ins for teammates' workflow steps (Week 7, Role 4).

The pipeline needs four steps that teammates are building:
    route(ticket)                         Role 1, workflow/routing.py
    start(ticket, now)                    Role 2, workflow/approvals.py
    escalate_overdue(tickets, now)        Role 2, workflow/approvals.py
    notify(event, ticket, resident_email=None, now=None)   Role 3, workflow/notify.py

Until each real function exists, the pipeline uses the simple version
below, written to the rules in the Week 7 role breakdown. As soon as a
teammate adds theirs, the pipeline uses it automatically, and the matching
stand-in here can be deleted. Nothing in this file is the final design.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTBOX_DIR = ROOT / "workflow" / "outbox"

# ---------- Role 1 stand-in: routing ----------
TEAMS = {"water": "Water", "sanitation": "Sanitation", "electricity": "Electricity",
         "streetlights": "Electricity", "roads": "Roads", "refuse": "Waste",
         "other": "Intake desk"}
DEPOTS = {"Old Alexandra": "West depot", "Pan Africa": "West depot",
          "East Bank": "East depot", "Far East Bank": "East depot",
          "Setswetla": "North depot", "Tsutsumani": "North depot"}
# Team assumption: the deadline depends only on urgency, never on the area,
# so quieter areas aren't given longer deadlines (Week 6 fairness finding).
SLA_HOURS = {5: 24, 4: 48, 3: 72, 2: 168, 1: 336}


def _parse(when) -> datetime:
    return when if isinstance(when, datetime) else datetime.fromisoformat(str(when))


def _iso(when: datetime) -> str:
    return when.isoformat(timespec="seconds")


def route(ticket: dict) -> dict:
    ticket = dict(ticket)
    urgency = int(ticket.get("urgency") or 2)
    ticket["assigned_team"] = TEAMS.get(str(ticket.get("category", "")).lower(), "Intake desk")
    ticket["depot"] = DEPOTS.get(ticket.get("ward"), "Central depot")
    ticket["sla_hours"] = SLA_HOURS.get(urgency, SLA_HOURS[2])
    ticket["due_by"] = _iso(_parse(ticket["received_at"]) + timedelta(hours=ticket["sla_hours"]))
    return ticket


# ---------- Role 2 stand-ins: approvals ----------
def _is_true(value) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1"}


def needs_approval(ticket: dict) -> bool:
    """Urgent (4-5) or unclear reports wait for a supervisor."""
    return int(ticket.get("urgency") or 0) >= 4 or _is_true(ticket.get("review_required"))


def start(ticket: dict, now) -> dict:
    ticket = dict(ticket)
    if needs_approval(ticket):
        ticket["status"], ticket["approval_status"] = "awaiting_approval", "pending"
    else:
        ticket["status"], ticket["approval_status"] = "assigned", "not_required"
    ticket["last_updated"] = _iso(_parse(now))
    return ticket


def escalate_overdue(tickets: list[dict], now) -> list[dict]:
    """Assigned or in-progress tickets past their deadline become escalated.
    Returns only the tickets that changed (as new dicts)."""
    now = _parse(now)
    changed = []
    for ticket in tickets:
        if ticket.get("status") not in {"assigned", "in_progress"} or not ticket.get("due_by"):
            continue
        if _parse(ticket["due_by"]) < now:
            updated = dict(ticket, status="escalated", last_updated=_iso(now))
            changed.append(updated)
    return changed


# ---------- Role 3 stand-in: notifications ----------
TEAM_ADDRESSES = {team: f"{team.lower().replace(' ', '.')}.team@example.org"
                  for team in set(TEAMS.values())}
SUPERVISOR_ADDRESS = "supervisor@example.org"
HIDDEN_RESIDENT = "Resident (address withheld) <withheld@example.invalid>"


def _mask(text: str) -> str:
    try:
        from governance.privacy import mask_personal_info
    except ImportError:  # never send anything if masking isn't available
        raise RuntimeError("governance/privacy.py is missing, so emails can't be masked")
    return mask_personal_info(text)


def notify(event: str, ticket: dict, resident_email: str | None = None, now=None):
    """Save one email as a .eml file in the outbox and return its path.
    Nothing is really sent. The resident's address is never written to disk:
    saved copies show it as withheld. Returns None when there's no one to tell."""
    tid = ticket.get("ticket_id", "")
    due = ticket.get("due_by", "")
    if event == "received":
        if not resident_email:
            return None
        to = HIDDEN_RESIDENT
        subject = f"We received your report ({tid})"
        body = (f"Thank you. Your report {tid} has been sent to the {ticket.get('assigned_team')} "
                f"team. We aim to fix it by {due}.")
    elif event == "assigned":
        to = TEAM_ADDRESSES.get(ticket.get("assigned_team"), SUPERVISOR_ADDRESS)
        subject = f"New ticket {tid}: urgency {ticket.get('urgency')}, {ticket.get('ward')}"
        body = (f"A new ticket has been assigned to your team.\n\nArea: {ticket.get('ward')}\n"
                f"Urgency: {ticket.get('urgency')}\nDue by: {due}\n\n{ticket.get('description_masked')}")
    elif event == "approval_needed":
        to = SUPERVISOR_ADDRESS
        why = ticket.get("decision_note") or (
            "the report is urgent" if int(ticket.get("urgency") or 0) >= 4
            else "the system could not sort it")
        subject = f"Approval needed: ticket {tid}"
        body = (f"Ticket {tid} is waiting for your decision because {why}.\n\n"
                f"Area: {ticket.get('ward')}\nTeam: {ticket.get('assigned_team')}\n\n"
                f"{ticket.get('description_masked')}")
    elif event == "overdue":
        to = SUPERVISOR_ADDRESS
        subject = f"Overdue: ticket {tid}"
        body = (f"Ticket {tid} ({ticket.get('assigned_team')} team, {ticket.get('ward')}) "
                f"was due by {due} and is not fixed yet.")
    else:
        raise ValueError(f"unknown email event: {event!r}")

    message = EmailMessage()
    message["From"] = "Report Radar <noreply@example.org>"
    message["To"] = to
    message["Subject"] = _mask(subject)
    message.set_content(_mask(body))
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _parse(now).strftime("%Y%m%d-%H%M%S") if now else datetime.now().strftime("%Y%m%d-%H%M%S")
    path = OUTBOX_DIR / f"{stamp}-{tid}-{event}.eml"
    path.write_bytes(bytes(message))
    return path
