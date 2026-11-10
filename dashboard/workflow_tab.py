"""Workflow tab for residents, service teams, and supervisors."""
from __future__ import annotations

import html
import importlib
import re
from datetime import datetime
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

WARDS = ["Old Alexandra", "East Bank", "Pan Africa", "Far East Bank",
         "Setswetla", "Tsutsumani"]
TEAMS = ["Water", "Sanitation", "Electricity", "Roads", "Waste", "Intake desk"]
ROOT = Path(__file__).resolve().parent.parent
TICKETS_FILE = ROOT / "workflow" / "data" / "tickets.csv"
OUTBOX_DIR = ROOT / "workflow" / "outbox"
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
FINAL_STATUSES = {"resolved", "closed", "rejected", "complete", "completed",
                  "cancelled", "canceled"}


def redact_emails(value) -> str:
    """Hide email addresses before any ticket or email text reaches the page."""
    return EMAIL_PATTERN.sub("[address hidden]", str(value or ""))


def _parse_datetime(value) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def friendly_date(iso) -> str:
    """Format an ISO date for the dashboard, for example '5 Nov, 08:15'."""
    parsed = _parse_datetime(iso)
    if parsed is None:
        return "Date not set"
    return f"{parsed.day} {parsed:%b}, {parsed:%H:%M}"


def _urgency(ticket: dict) -> int:
    value = str(ticket.get("urgency", "")).strip().lower()
    match = re.search(r"\d+", value)
    if match:
        return int(match.group())
    return {"critical": 5, "urgent": 4, "high": 4, "medium": 3,
            "low": 2, "cosmetic": 1}.get(value, 0)


def _is_open(ticket: dict) -> bool:
    return str(ticket.get("status", "open")).strip().lower().replace(" ", "_") not in {
        status.replace(" ", "_") for status in FINAL_STATUSES
    }


def _deadline_order(ticket: dict) -> float:
    deadline = _parse_datetime(ticket.get("due_by"))
    if deadline is None:
        return float("inf")
    try:
        return deadline.timestamp()
    except (OSError, OverflowError, ValueError):
        return float("inf")


def queue_for_team(tickets: list[dict], team: str) -> list[dict]:
    """Return a team's open tickets, most urgent and then soonest due first."""
    selected = [ticket for ticket in tickets
                if str(ticket.get("assigned_team", "")).strip().casefold()
                == str(team).strip().casefold() and _is_open(ticket)]
    return sorted(selected, key=lambda ticket: (-_urgency(ticket), _deadline_order(ticket)))


def is_overdue(ticket: dict, now: datetime | None = None) -> bool:
    """Whether an open ticket's expected fix time has passed."""
    deadline = _parse_datetime(ticket.get("due_by"))
    if deadline is None or not _is_open(ticket):
        return False
    current = now or datetime.now().astimezone()
    try:
        return deadline.timestamp() < current.timestamp()
    except (OSError, OverflowError, ValueError):
        return False


def waiting_for_approval(tickets: list[dict]) -> list[dict]:
    """Find tickets that still need a supervisor decision."""
    pending = {"pending", "waiting", "required", "needs_review", "needs review",
               "awaiting_approval", "pending_approval"}
    finished = {"approved", "rejected", "complete", "completed", "not_required"}
    result = []
    for ticket in tickets:
        approval = str(ticket.get("approval_status", "")).strip().lower()
        status = str(ticket.get("status", "")).strip().lower().replace(" ", "_")
        review_required = str(ticket.get("review_required", "")).strip().lower() in {
            "true", "yes", "1", "required"
        }
        if approval in finished or status in {"rejected", "resolved", "closed"}:
            continue
        if approval in pending or (review_required and not approval):
            result.append(ticket)
    return result


def latest_emails(outbox: Path = OUTBOX_DIR, limit: int = 10) -> list[dict] | None:
    """Read recent .eml files; return None if the outbox does not exist."""
    if not outbox.is_dir():
        return None
    files = sorted(outbox.glob("*.eml"), key=lambda path: path.stat().st_mtime,
                   reverse=True)
    messages = []
    for path in files[:limit]:
        try:
            with path.open("rb") as source:
                message = BytesParser(policy=policy.default).parse(source)
            subject = redact_emails(message.get("Subject", "No subject"))
            recipients = getaddresses([str(message.get("To", ""))])
            names = [redact_emails(name).strip() for name, address in recipients if name.strip()]
            to_whom = ", ".join(names) if names else (
                "Recipient (address hidden)" if recipients else "Recipient not listed"
            )
            sent_at = None
            if message.get("Date"):
                try:
                    sent_at = parsedate_to_datetime(str(message.get("Date"))).isoformat()
                except (TypeError, ValueError, OverflowError):
                    sent_at = None
            if sent_at is None:
                sent_at = datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat()
            body_parts = []
            for part in message.walk():
                if part.get_content_type() == "text/plain" and not part.get_content_disposition() == "attachment":
                    try:
                        body_parts.append(str(part.get_content()))
                    except (LookupError, UnicodeDecodeError):
                        continue
            body = "\n\n".join(body_parts).strip()
            if not body and message.get_content_type() == "text/html":
                try:
                    body = re.sub(r"<[^>]*>", " ", str(message.get_content()))
                except (LookupError, UnicodeDecodeError):
                    body = ""
            messages.append({"subject": subject or "No subject",
                             "to": redact_emails(to_whom),
                             "when": friendly_date(sent_at),
                             "body": redact_emails(html.unescape(body)) or "No message text."})
        except (OSError, ValueError):
            continue
    return messages


def _optional_function(module_name: str, function_name: str):
    try:
        return getattr(importlib.import_module(module_name), function_name, None)
    except ImportError:
        return None


def _load_tickets() -> tuple[list[dict] | None, str | None]:
    load = _optional_function("workflow.pipeline", "load_tickets")
    if load is None:
        return None, "The ticket list is not ready yet; the ticket-loading step is still being added."
    try:
        tickets = load()
    except (OSError, ValueError, ImportError):
        return None, "We could not load the ticket list yet. Please try again later."
    if not isinstance(tickets, list):
        return None, "The ticket list is not available yet."
    return [ticket for ticket in tickets if isinstance(ticket, dict)], None


def _ticket_id(ticket: dict) -> str:
    return redact_emails(ticket.get("ticket_id") or "Not assigned")


def _display(value, fallback: str = "Not provided") -> str:
    return redact_emails(value).strip() or fallback


def _approval_action(record_decision, ticket: dict, approver: str, decision: str,
                     note: str, team: str | None = None) -> dict:
    """Save a supervisor decision through the pipeline, which also emails the team and logs it."""
    return record_decision(ticket, approver.strip(), decision, note.strip(), new_team=team)


def _saved(message: str) -> None:
    """Show the message after reloading, so the decided ticket leaves the list."""
    import streamlit as st

    st.session_state["workflow_saved"] = message
    st.rerun()


def _show_report_form() -> None:
    import streamlit as st

    process_report = _optional_function("workflow.pipeline", "process_report")
    st.subheader("Report a problem")
    if process_report is None:
        st.info("Report submission is not ready yet. The workflow team is still adding the report form connection.")
    with st.form("workflow_report_form", clear_on_submit=True):
        description = st.text_area("What's wrong?", max_chars=2000)
        ward = st.selectbox("Which area?", WARDS)
        email = st.text_input("Email for updates (optional)",
                              help="Only used to send updates about this report.")
        st.caption("Email is optional and is only used to send updates about this report.")
        submitted = st.form_submit_button("Send report", disabled=process_report is None)
    if submitted:
        if not description.strip():
            st.error("Please describe the problem before sending the report.")
        elif email.strip() and not EMAIL_PATTERN.fullmatch(email.strip()):
            st.error("That email address does not look complete. Fix it or leave it blank.")
        else:
            try:
                ticket = process_report(description.strip(), ward,
                                        resident_email=email.strip() or None)
                if not isinstance(ticket, dict):
                    raise ValueError("The report did not return a ticket")
                st.success(
                    f"Report sent. Ticket number: {_ticket_id(ticket)}. "
                    f"Team: {_display(ticket.get('assigned_team'), 'Being assigned')}. "
                    f"Expected fix date: {friendly_date(ticket.get('due_by'))}."
                )
            except Exception:
                st.error("We could not send the report just now. Your email has not been shown. Please try again.")


def _show_team_queue(tickets: list[dict] | None, error: str | None) -> None:
    import streamlit as st

    st.subheader("My team's queue")
    team = st.selectbox("Choose your team", TEAMS, key="workflow_queue_team")
    if tickets is None:
        st.info(error or "The ticket list is not ready yet.")
        return
    queue = queue_for_team(tickets, team)
    if not queue:
        st.info(f"There are no open tickets for {team} right now.")
        return
    rows = []
    for ticket in queue:
        due = ticket.get("due_by")
        overdue = is_overdue(ticket)
        status = "Overdue" if overdue else str(ticket.get("status", "Open")).replace("_", " ").title()
        rows.append({
            "Ticket": _ticket_id(ticket),
            "Problem": _display(ticket.get("description_masked")),
            "Area": _display(ticket.get("ward")),
            "Urgency": str(ticket.get("urgency", "Not set")),
            "Expected fix": friendly_date(due),
            "Status": status,
        })
        if overdue:
            st.warning(f"Ticket {_ticket_id(ticket)} is overdue. Expected fix: {friendly_date(due)}.")
    st.dataframe(rows, hide_index=True, width="stretch")


def _show_approvals(tickets: list[dict] | None, error: str | None) -> None:
    import streamlit as st

    st.subheader("Waiting for approval")
    if tickets is None:
        st.info(error or "The ticket list is not ready yet.")
        return
    pending = waiting_for_approval(tickets)
    if not pending:
        st.info("There are no reports waiting for a supervisor decision.")
        return
    saved = st.session_state.pop("workflow_saved", None)
    if saved:
        st.success(saved)
    decide = _optional_function("workflow.pipeline", "record_decision")
    if decide is None:
        st.info("Supervisor decisions are not ready yet; the decision-saving step is still being added.")
    approver = st.text_input("Your name", key="workflow_approver")
    for index, ticket in enumerate(pending):
        ticket_id = _ticket_id(ticket)
        key_id = re.sub(r"[^A-Za-z0-9_-]", "_", ticket_id)
        action_key = f"workflow_action_{key_id}_{index}"
        with st.expander(f"Ticket {ticket_id} · {_display(ticket.get('ward'))}"):
            st.write(_display(ticket.get("description_masked")))
            st.caption(f"Team: {_display(ticket.get('assigned_team'))} · "
                       f"Urgency: {_display(ticket.get('urgency'))}")
            if ticket.get("approver"):
                st.caption(f"Last decision by {_display(ticket.get('approver'))} · "
                           f"{friendly_date(ticket.get('last_updated'))}")
            approve_col, reassign_col, reject_col = st.columns(3)
            disabled = decide is None or not approver.strip()
            if approve_col.button("Approve", key=f"approve_{key_id}_{index}", disabled=disabled):
                try:
                    _approval_action(decide, ticket, approver, "approve", "")
                except Exception:
                    st.error("We could not save that decision. Please try again.")
                else:
                    _saved(f"Ticket {ticket_id} approved. The team has been emailed.")
            if reassign_col.button("Reassign", key=f"reassign_{key_id}_{index}", disabled=disabled):
                st.session_state[action_key] = "reassign"
            if reject_col.button("Reject", key=f"reject_{key_id}_{index}", disabled=disabled):
                st.session_state[action_key] = "reject"
            action = st.session_state.get(action_key)
            if action == "reassign":
                new_team = st.selectbox("Send to team", TEAMS, key=f"team_{key_id}_{index}")
                reason = st.text_input("Why are you reassigning it?", key=f"reason_{key_id}_{index}")
                if st.button("Save reassignment", key=f"save_reassign_{key_id}_{index}",
                             disabled=decide is None or not approver.strip() or not reason.strip()):
                    try:
                        _approval_action(decide, ticket, approver, "reassign", reason, new_team)
                        st.session_state.pop(action_key, None)
                    except Exception:
                        st.error("We could not save that decision. Please try again.")
                    else:
                        _saved(f"Ticket {ticket_id} sent to {new_team}. The team has been emailed.")
            elif action == "reject":
                reason = st.text_input("Why are you rejecting it?", key=f"reason_{key_id}_{index}")
                if st.button("Save rejection", key=f"save_reject_{key_id}_{index}",
                             disabled=decide is None or not approver.strip() or not reason.strip()):
                    try:
                        _approval_action(decide, ticket, approver, "reject", reason)
                        st.session_state.pop(action_key, None)
                    except Exception:
                        st.error("We could not save that decision. Please try again.")
                    else:
                        _saved(f"Ticket {ticket_id} rejected.")


def _show_sent_emails() -> None:
    import streamlit as st

    st.subheader("Sent emails")
    emails = latest_emails()
    if emails is None:
        st.info("The email outbox is not ready yet. It will appear when workflow/notify.py is added.")
        return
    if not emails:
        st.info("No emails have been sent yet.")
        return
    for index, message in enumerate(emails):
        label = f"{message['subject']} · To: {message['to']} · {message['when']}"
        with st.expander(label, key=f"workflow_email_{index}"):
            st.text(message["body"])


def _load_examples_if_empty() -> int:
    """On a fresh copy (like the live site) there are no tickets yet: run the 10
    example reports through the real workflow once, so every section has data."""
    load = _optional_function("workflow.pipeline", "load_demo_tickets_if_empty")
    if load is None:
        return 0
    try:
        return load()
    except Exception:  # never stop the tab from opening because of the examples
        return 0


def example_note(tickets: list[dict] | None, example_ids: set[str]) -> str | None:
    """A plain-words note when some of the tickets shown are made-up examples."""
    count = sum(1 for ticket in tickets or [] if ticket.get("ticket_id") in example_ids)
    if not count:
        return None
    return (f"{count} of these tickets are made-up example reports, loaded so every section "
            "has something to show. Reports you submit above are added to them.")


def _show_example_note(tickets: list[dict] | None) -> None:
    import streamlit as st

    ids = _optional_function("workflow.pipeline", "demo_ticket_ids")
    try:
        note = example_note(tickets, ids() if ids else set())
    except (OSError, ValueError, KeyError):
        note = None
    if note:
        st.info(note)


def show_workflow_tab() -> None:
    """Draw the four workflow sections; each optional dependency can be absent."""
    import streamlit as st

    st.header("Workflow")
    _load_examples_if_empty()
    _show_report_form()
    tickets, error = _load_tickets()
    _show_example_note(tickets)
    _show_team_queue(tickets, error)
    _show_approvals(tickets, error)
    _show_sent_emails()