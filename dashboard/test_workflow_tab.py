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


def test_empty_pipeline_module_has_a_friendly_not_ready_message(monkeypatch):
    import workflow_tab
    # Simulate workflow/pipeline.py without load_tickets (as before the pipeline was built)
    monkeypatch.setattr(workflow_tab, "_optional_function", lambda module, name: None)
    tickets, message = _load_tickets()

    assert tickets is None
    assert "ticket-loading step is still being added" in message


def test_real_pipeline_tickets_are_loaded(tmp_path, monkeypatch):
    from workflow import pipeline
    monkeypatch.setattr(pipeline, "TICKETS_FILE", tmp_path / "tickets.csv")
    pipeline.save_ticket({"ticket_id": "TKT-000001", "assigned_team": "Water", "status": "assigned"})
    tickets, message = _load_tickets()

    assert message is None
    assert [t["ticket_id"] for t in tickets] == ["TKT-000001"]

def test_approval_buttons_save_through_the_pipeline(tmp_path, monkeypatch):
    from workflow import pipeline
    from workflow_tab import _approval_action
    monkeypatch.setattr(pipeline, "TICKETS_FILE", tmp_path / "tickets.csv")
    calls = []
    record = lambda *args, **kwargs: calls.append((args, kwargs))
    ticket = {"ticket_id": "TKT-000001", "status": "awaiting_approval"}

    _approval_action(record, ticket, " Sup ", "reassign", " Wrong team ", "Roads")

    assert calls == [((ticket, "Sup", "reassign", "Wrong team"), {"new_team": "Roads"})]
