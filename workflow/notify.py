"""Role 3: email notifications.

Four events: received (resident), assigned (team), approval_needed and overdue
(supervisor). Every email is masked before it is saved or sent.

By default nothing is really sent: each email is saved as a .eml file in the
outbox. It is only sent for real if SMTP_HOST, SMTP_USER and SMTP_PASSWORD are
ALL set. The resident's address is never written to disk, the ticket or the log.
"""
from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from governance.logger import log_decision
from governance.privacy import mask_personal_info

try:
    from workflow import fallbacks
except ImportError:  # running from inside the workflow folder
    import fallbacks

EVENTS = ("received", "assigned", "approval_needed", "overdue")

# None means "use the same outbox folder as the pipeline". Tests point this elsewhere.
OUTBOX_DIR = None


# ---------- small helpers ----------
def _to_dt(value) -> datetime:
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return dt.replace(tzinfo=None)  # compare times without worrying about time zones


def _friendly(value) -> str:
    """'2026-11-05T08:15:00' -> '5 Nov, 08:15'"""
    try:
        dt = _to_dt(value)
    except (TypeError, ValueError):
        return "a date still to be confirmed"
    return f"{dt.day} {dt:%b}, {dt:%H:%M}"


def _yes(value) -> bool:
    return str(value).strip().lower() in ("true", "yes", "1")


def _urgency(ticket: dict) -> int:
    try:
        return int(ticket.get("urgency") or 0)
    except (TypeError, ValueError):
        return 0


def _why_approval(ticket: dict) -> str:
    reasons = []
    if _urgency(ticket) >= 4:
        reasons.append("the report is urgent")
    if _yes(ticket.get("review_required")):
        reasons.append("the system was not sure how to sort it")
    return " and ".join(reasons) or "it needs a second pair of eyes"


def _hours_overdue(ticket: dict, now) -> int:
    try:
        due = _to_dt(ticket.get("due_by"))
        current = _to_dt(now) if now else datetime.now()
        return max(0, int((current - due).total_seconds() // 3600))
    except (TypeError, ValueError):
        return 0


# ---------- the four emails ----------
def _compose(event: str, ticket: dict, now):
    """Returns (recipient_role, subject, body). Plain words, ASCII only."""
    tid = ticket.get("ticket_id", "")
    team = ticket.get("assigned_team") or "Intake desk"
    ward = ticket.get("ward") or "unknown area"
    due = _friendly(ticket.get("due_by"))
    description = ticket.get("description_masked") or ""

    if event == "received":
        return ("resident",
                f"We received your report ({tid})",
                f"Thank you for your report.\n\nYour ticket number is {tid}.\n"
                f"It has been sent to the {team} team.\n"
                f"We aim to fix it by {due}.\n")
    if event == "assigned":
        return ("team",
                f"New ticket {tid}: urgency {ticket.get('urgency')}, {ward}",
                f"A new ticket has been assigned to your team.\n\n"
                f"Ticket: {tid}\nUrgency: {ticket.get('urgency')} (5 is most urgent)\n"
                f"Area: {ward}\nDue by: {due}\n\nWhat was reported:\n{description}\n")
    if event == "approval_needed":
        return ("supervisor",
                f"Approval needed: ticket {tid}",
                f"Ticket {tid} is waiting for your decision because {_why_approval(ticket)}.\n\n"
                f"Area: {ward}\nTeam: {team}\nDue by: {due}\n\n"
                f"What was reported:\n{description}\n")
    hours = _hours_overdue(ticket, now)  # event == "overdue"
    return ("supervisor",
            f"Overdue: ticket {tid}",
            f"Ticket {tid} ({team} team, {ward}) was due by {due} and is not fixed yet.\n"
            f"It is now about {hours} hours overdue.\n")


def _address_for(role: str, ticket: dict) -> str:
    if role == "resident":
        return fallbacks.HIDDEN_RESIDENT
    if role == "team":
        return fallbacks.TEAM_ADDRESSES.get(ticket.get("assigned_team"), fallbacks.SUPERVISOR_ADDRESS)
    return fallbacks.SUPERVISOR_ADDRESS


def _build(to: str, subject: str, body: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = "Report Radar <noreply@example.org>"
    message["To"] = to
    message["Subject"] = mask_personal_info(subject)
    message.set_content(mask_personal_info(body))
    return message


# ---------- sending ----------
def _smtp_settings():
    host, user, password = (os.environ.get(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))
    return (host, user, password) if host and user and password else None


def _send(message: EmailMessage, settings) -> None:
    host, user, password = settings
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(message)


# ---------- the one function the pipeline calls ----------
def notify(event: str, ticket: dict, resident_email: str | None = None, now=None):
    """Save (and, only if SMTP is fully set up, send) one email. Returns the saved file's path,
    or None when there is nobody to tell."""
    if event not in EVENTS:
        raise ValueError(f"unknown email event: {event!r}")
    if event == "received" and not (resident_email and "@" in resident_email):
        return None  # no address given, so no email

    role, subject, body = _compose(event, ticket, now)

    # The saved copy never contains the resident's real address.
    saved = _build(_address_for(role, ticket), subject, body)
    outbox = OUTBOX_DIR or fallbacks.OUTBOX_DIR
    outbox.mkdir(parents=True, exist_ok=True)
    stamp = (_to_dt(now) if now else datetime.now()).strftime("%Y%m%d-%H%M%S")
    path = outbox / f"{stamp}-{ticket.get('ticket_id', '')}-{event}.eml"
    path.write_bytes(bytes(saved))

    mode = "outbox"
    settings = _smtp_settings()
    if settings:
        try:
            to = resident_email if role == "resident" else _address_for(role, ticket)
            _send(_build(to, subject, body), settings)
            mode = "smtp"
        except Exception:  # an email problem must never lose or park a ticket
            mode = "outbox (smtp failed)"

    # Log the recipient ROLE, never an address.
    log_decision("notifications", ticket.get("ticket_id", ""), event, f"sent to: {role}", mode)
    return path
