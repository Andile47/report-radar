"""Approval decisions and status transitions for Report Radar tickets."""

from __future__ import annotations

from datetime import datetime, timezone
from statistics import median

from governance.logger import log_decision

STATUSES = {
	"new",
	"awaiting_approval",
	"assigned",
	"in_progress",
	"escalated",
	"resolved",
	"rejected",
}

ALLOWED_MOVES = {
	"new": {"awaiting_approval", "assigned"},
	"awaiting_approval": {"assigned", "rejected"},
	"assigned": {"in_progress", "escalated"},
	"in_progress": {"resolved", "escalated"},
	"escalated": {"awaiting_approval", "assigned", "in_progress"},
	"resolved": set(),
	"rejected": set(),
}


def _timestamp(value) -> datetime:
	"""Parse an ISO timestamp and make naive values comparable as UTC."""
	parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
	if parsed.tzinfo is None:
		return parsed.replace(tzinfo=timezone.utc)
	return parsed


def _iso(value) -> str:
	return _timestamp(value).isoformat(timespec="seconds")


def _log(ticket: dict, output: str, reason: str) -> None:
	log_decision(
		"approvals",
		ticket.get("ticket_id"),
		ticket.get("description_masked", ""),
		output,
		reason,
	)


def move(ticket: dict, new_status: str, when) -> dict:
	"""Return a copied ticket with an allowed status transition applied."""
	old_status = ticket.get("status")
	if old_status not in ALLOWED_MOVES or new_status not in ALLOWED_MOVES.get(old_status, set()):
		raise ValueError(f"Status move from '{old_status}' to '{new_status}' is not allowed")
	return {**ticket, "status": new_status, "last_updated": _iso(when)}


def needs_approval(ticket: dict) -> bool:
	"""Whether urgency, uncertainty, or a hand-edited team needs review."""
	try:
		urgent = int(ticket.get("urgency", 0)) >= 4
	except (TypeError, ValueError):
		urgent = False
	review_required = str(ticket.get("review_required", "")).strip().lower() in {
		"true", "1", "yes",
	}
	team_changed_by_hand = str(ticket.get("team_changed_by_hand", "")).strip().lower() in {
		"true", "1", "yes",
	}
	return urgent or review_required or team_changed_by_hand


def start(ticket: dict, now) -> dict:
	"""Send a new ticket to approval or assignment, and log the decision."""
	if needs_approval(ticket):
		updated = move(ticket, "awaiting_approval", now)
		updated["approval_status"] = "pending"
		reason = "Supervisor approval required"
	else:
		updated = move(ticket, "assigned", now)
		updated["approval_status"] = "not_required"
		reason = "Supervisor approval not required"
	_log(updated, f"status={updated['status']}; approval_status={updated['approval_status']}", reason)
	return updated


def decide(ticket: dict, approver: str, decision: str, note: str, now,
		   new_team: str | None = None) -> dict:
	"""Record an approval decision; reassignment requires its new team and a note."""
	decision = str(decision).strip().lower()
	note = "" if note is None else str(note).strip()
	if decision not in {"approve", "reassign", "reject"}:
		raise ValueError("Decision must be 'approve', 'reassign', or 'reject'")
	if decision in {"reassign", "reject"} and not note:
		raise ValueError(f"A written note is required to {decision}")
	if decision == "reassign" and not str(new_team or "").strip():
		raise ValueError("A new team is required to reassign")

	new_status = "rejected" if decision == "reject" else "assigned"
	updated = move(ticket, new_status, now)
	updated["approver"] = approver
	updated["decision_note"] = note
	updated["approval_status"] = {
		"approve": "approved",
		"reassign": "reassigned",
		"reject": "rejected",
	}[decision]
	if decision == "reassign":
		updated["assigned_team"] = str(new_team).strip()
	_log(updated, f"decision={decision}; status={new_status}", note or "Supervisor approved")
	return updated


def escalate_overdue(tickets: list[dict], now) -> list[dict]:
	"""Return overdue assigned or active tickets as escalated copies."""
	current_time = _timestamp(now)
	changed = []
	for ticket in tickets:
		if ticket.get("status") not in {"assigned", "in_progress"}:
			continue
		try:
			due = _timestamp(ticket.get("due_by"))
		except (TypeError, ValueError):
			continue
		if due >= current_time:
			continue
		updated = move(ticket, "escalated", now)
		changed.append(updated)
		_log(updated, "status=escalated", f"Overdue; due_by={ticket.get('due_by')}")
	return changed


def fairness_flags(tickets: list[dict]) -> list[str]:
	"""Return wards over 1.5 times the fastest resolved-urgent median."""
	hours_by_ward: dict[str, list[float]] = {}
	for ticket in tickets:
		try:
			urgent = int(ticket.get("urgency", 0)) >= 4
			if not urgent or str(ticket.get("status", "")).strip().lower() != "resolved":
				continue
			received = _timestamp(ticket.get("received_at"))
			resolved = _timestamp(ticket.get("last_updated"))
			hours = (resolved - received).total_seconds() / 3600
			if hours < 0:
				continue
			ward = str(ticket.get("ward", "")).strip()
			if ward:
				hours_by_ward.setdefault(ward, []).append(hours)
		except (TypeError, ValueError):
			continue

	medians = {ward: median(values) for ward, values in hours_by_ward.items()}
	if not medians:
		return []
	threshold = min(medians.values()) * 1.5
	return sorted(ward for ward, wait in medians.items() if wait > threshold)

