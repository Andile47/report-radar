"""Tests for the workflow tab's plain-Python helpers."""
from datetime import datetime, timezone

from workflow_tab import (friendly_date, is_overdue, queue_for_team,
                          redact_emails, waiting_for_approval, _load_tickets)


def ticket(ticket_id, urgency, due_by, **changes):
    return {"ticket_id": ticket_id, "assigned_team": "Water", "urgency": urgency,
            "due_by": due_by, "status": "open", **changes}


def test_queue_sorts_by_urgency_then_nearest_deadline():
    tickets = [
        ticket("later", 4, "2026-11-06T09:00:00+00:00"),
        ticket("sooner", 4, "2026-11-05T08:15:00+00:00"),
        ticket("most urgent", 5, "2026-11-07T10:00:00+00:00"),
        ticket("closed", 5, "2026-11-04T08:00:00+00:00", status="resolved"),
        ticket("other team", 5, "2026-11-04T08:00:00+00:00", assigned_team="Roads"),
    ]

    assert [item["ticket_id"] for item in queue_for_team(tickets, "water")] == [
        "most urgent", "sooner", "later"
    ]


def test_friendly_date_uses_day_month_and_24_hour_time():
    assert friendly_date("2026-11-05T08:15:00+02:00") == "5 Nov, 08:15"
    assert friendly_date("not-a-date") == "Date not set"


def test_overdue_only_marks_open_tickets_past_the_deadline():
    now = datetime(2026, 11, 5, 9, 0, tzinfo=timezone.utc)
    assert is_overdue(ticket("late", 3, "2026-11-05T08:15:00+00:00"), now)
    assert not is_overdue(ticket("closed", 3, "2026-11-05T08:15:00+00:00",
                                 status="resolved"), now)


def test_waiting_for_approval_uses_review_flag_and_pending_status():
    tickets = [
        ticket("flagged", 2, "", review_required="true"),
        ticket("pending", 2, "", approval_status="pending"),
        ticket("done", 2, "", approval_status="approved", review_required="true"),
    ]

    assert [item["ticket_id"] for item in waiting_for_approval(tickets)] == [
        "flagged", "pending"
    ]


def test_email_addresses_are_hidden_from_display_text():
    assert redact_emails("Resident jane@example.org reported an issue") == (
        "Resident [address hidden] reported an issue"
    )


def test_empty_pipeline_module_has_a_friendly_not_ready_message():
    tickets, message = _load_tickets()

    assert tickets is None
    assert "ticket-loading step is still being added" in message