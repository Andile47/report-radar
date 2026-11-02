"""Tests for the temporary workflow stand-ins. Delete each part when the real module lands."""
import sys
from email import policy
from email.parser import BytesParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workflow import fallbacks as fb  # noqa: E402

NOW = "2026-11-03T08:00:00+02:00"


def ticket(**changes):
    base = {"ticket_id": "TKT-000001", "received_at": NOW, "ward": "Tsutsumani",
            "category": "water", "urgency": 3, "review_required": False,
            "description_masked": "No water since this morning"}
    return {**base, **changes}


def test_every_category_has_a_team_and_unknowns_go_to_the_intake_desk():
    assert fb.route(ticket(category="streetlights"))["assigned_team"] == "Electricity"
    assert fb.route(ticket(category="refuse"))["assigned_team"] == "Waste"
    assert fb.route(ticket(category="parking"))["assigned_team"] == "Intake desk"
    assert fb.route(ticket(ward="Somewhere else"))["depot"] == "Central depot"


def test_same_urgency_gets_the_same_deadline_in_every_area():
    quiet = fb.route(ticket(ward="Tsutsumani", urgency=5))
    busy = fb.route(ticket(ward="Old Alexandra", urgency=5))
    assert quiet["due_by"] == busy["due_by"] == "2026-11-04T08:00:00+02:00"


def test_urgent_or_unclear_tickets_wait_for_approval():
    assert fb.start(ticket(urgency=5), NOW)["approval_status"] == "pending"
    assert fb.start(ticket(review_required="True"), NOW)["status"] == "awaiting_approval"
    minor = fb.start(ticket(urgency=2), NOW)
    assert (minor["status"], minor["approval_status"]) == ("assigned", "not_required")


def test_only_late_open_tickets_are_escalated():
    late = dict(ticket(), status="assigned", due_by="2026-11-02T08:00:00+02:00")
    on_time = dict(ticket(ticket_id="TKT-000002"), status="assigned", due_by="2026-11-09T08:00:00+02:00")
    done = dict(late, ticket_id="TKT-000003", status="resolved")
    changed = fb.escalate_overdue([late, on_time, done], NOW)
    assert [(t["ticket_id"], t["status"]) for t in changed] == [("TKT-000001", "escalated")]
    assert late["status"] == "assigned"  # the original is not changed


@pytest.fixture
def outbox(tmp_path, monkeypatch):
    monkeypatch.setattr(fb, "OUTBOX_DIR", tmp_path)
    return tmp_path


def read(path):
    return BytesParser(policy=policy.default).parse(path.open("rb"))


def test_emails_are_masked_and_never_hold_the_residents_address(outbox):
    t = fb.route(ticket(description_masked="No water, call 082 123 4567"))
    team = read(fb.notify("assigned", t, now=NOW))
    assert "082 123 4567" not in team.get_content() and "[PHONE]" in team.get_content()
    resident = fb.notify("received", t, resident_email="resident@example.com", now=NOW)
    assert "resident@example.com" not in resident.read_text()
    assert fb.notify("received", t, resident_email=None, now=NOW) is None


def test_unknown_email_event_is_an_error(outbox):
    with pytest.raises(ValueError):
        fb.notify("party", ticket(), now=NOW)
