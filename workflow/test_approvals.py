from datetime import datetime, timedelta, timezone

import pytest

from workflow import approvals


NOW = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def silence_decision_log(monkeypatch):
    monkeypatch.setattr(approvals, "log_decision", lambda *args, **kwargs: 0)


def make_ticket(status="new", **changes):
    return {
        "ticket_id": "TKT-000001",
        "status": status,
        "urgency": 2,
        "review_required": False,
        "assigned_team": "Water",
        "due_by": "2026-11-02T13:00:00+00:00",
        "received_at": "2026-11-02T08:00:00+00:00",
        "last_updated": "2026-11-02T08:00:00+00:00",
        "ward": "Fast Ward",
        **changes,
    }


@pytest.mark.parametrize(
    ("old_status", "new_status"),
    [
        ("new", "awaiting_approval"),
        ("new", "assigned"),
        ("awaiting_approval", "assigned"),
        ("awaiting_approval", "rejected"),
        ("assigned", "in_progress"),
        ("assigned", "escalated"),
        ("in_progress", "resolved"),
        ("in_progress", "escalated"),
        ("escalated", "awaiting_approval"),
        ("escalated", "assigned"),
        ("escalated", "in_progress"),
    ],
)
def test_every_allowed_move_returns_an_updated_copy(old_status, new_status):
    original = make_ticket(status=old_status)

    updated = approvals.move(original, new_status, NOW)

    assert updated is not original
    assert updated["status"] == new_status
    assert updated["last_updated"] == NOW.isoformat(timespec="seconds")
    assert original["status"] == old_status


def test_final_status_cannot_move_to_assigned():
    with pytest.raises(ValueError, match="resolved.*assigned"):
        approvals.move(make_ticket(status="resolved"), "assigned", NOW)


def test_urgent_and_unclear_tickets_need_approval_but_minor_clear_one_does_not():
    assert approvals.needs_approval(make_ticket(urgency=4))
    assert approvals.needs_approval(make_ticket(review_required="true"))
    assert approvals.needs_approval(make_ticket(team_changed_by_hand=True))
    assert not approvals.needs_approval(make_ticket(urgency=2))


def test_start_sets_approval_status_without_changing_original_ticket():
    urgent = make_ticket(urgency=5)
    minor = make_ticket(urgency=1)

    waiting = approvals.start(urgent, NOW)
    assigned = approvals.start(minor, NOW)

    assert waiting["status"] == "awaiting_approval"
    assert waiting["approval_status"] == "pending"
    assert assigned["status"] == "assigned"
    assert assigned["approval_status"] == "not_required"
    assert urgent["status"] == minor["status"] == "new"


def test_reject_requires_note_and_records_the_decision():
    ticket = make_ticket(status="awaiting_approval")

    with pytest.raises(ValueError, match="written note"):
        approvals.decide(ticket, "Supervisor", "reject", "", NOW)

    rejected = approvals.decide(ticket, "Supervisor", "reject", "Duplicate report", NOW)

    assert rejected["status"] == "rejected"
    assert rejected["approval_status"] == "rejected"
    assert rejected["approver"] == "Supervisor"
    assert rejected["decision_note"] == "Duplicate report"
    assert ticket["status"] == "awaiting_approval"


def test_reassignment_requires_note_and_new_team():
    ticket = make_ticket(status="awaiting_approval")

    with pytest.raises(ValueError, match="written note"):
        approvals.decide(ticket, "Supervisor", "reassign", "", NOW, new_team="Roads")
    with pytest.raises(ValueError, match="new team"):
        approvals.decide(ticket, "Supervisor", "reassign", "Wrong queue", NOW)

    reassigned = approvals.decide(
        ticket, "Supervisor", "reassign", "Water team cannot handle this", NOW,
        new_team="Roads",
    )

    assert reassigned["status"] == "assigned"
    assert reassigned["approval_status"] == "reassigned"
    assert reassigned["assigned_team"] == "Roads"
    assert ticket["assigned_team"] == "Water"


def test_escalate_overdue_moves_only_late_assigned_or_active_tickets():
    overdue_assigned = make_ticket(status="assigned", due_by="2026-11-02T11:00:00+00:00")
    overdue_active = make_ticket(status="in_progress", due_by="2026-11-02T11:00:00+00:00")
    on_time = make_ticket(status="assigned", due_by="2026-11-02T13:00:00+00:00")

    changed = approvals.escalate_overdue([overdue_assigned, overdue_active, on_time], NOW)

    assert [ticket["status"] for ticket in changed] == ["escalated", "escalated"]
    assert overdue_assigned["status"] == "assigned"
    assert overdue_active["status"] == "in_progress"
    assert on_time["status"] == "assigned"


def test_fairness_flags_uses_urgent_resolution_medians_and_strict_threshold():
    def resolved_ticket(ward, hours):
        received = NOW - timedelta(hours=hours)
        return make_ticket(
            status="resolved",
            urgency=4,
            ward=ward,
            received_at=received.isoformat(),
            last_updated=NOW.isoformat(),
        )

    tickets = [
        resolved_ticket("Fast Ward", 4),
        resolved_ticket("Fast Ward", 6),
        resolved_ticket("At Threshold", 6),
        resolved_ticket("At Threshold", 9),
        resolved_ticket("Slow Ward", 8),
        resolved_ticket("Slow Ward", 12),
    ]
    tickets.append(make_ticket(status="resolved", urgency=2, ward="Not Urgent", received_at=(NOW - timedelta(hours=40)).isoformat()))

    assert approvals.fairness_flags(tickets) == ["Slow Ward"]