"""Tests for the Week 7 workflow pipeline. Run from the repo root:  pytest workflow"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workflow import pipeline  # noqa: E402


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A temporary tickets file, so tests never touch the real one."""
    path = tmp_path / "tickets.csv"
    monkeypatch.setattr(pipeline, "TICKETS_FILE", path)
    return path


def test_no_tickets_file_means_no_tickets(store):
    assert pipeline.load_tickets() == []


def test_saved_ticket_is_loaded_with_the_agreed_columns_only(store):
    pipeline.save_ticket({"ticket_id": "TKT-000001", "ward": "Tsutsumani", "urgency": 4,
                          "resident_email": "someone@example.com"})
    assert store.read_text().splitlines()[0] == ",".join(pipeline.COLUMNS)
    [ticket] = pipeline.load_tickets()
    assert list(ticket) == pipeline.COLUMNS
    assert ticket["ward"] == "Tsutsumani" and ticket["urgency"] == "4"
    assert "someone@example.com" not in store.read_text()


def test_saving_the_same_ticket_again_updates_it(store):
    pipeline.save_ticket({"ticket_id": "TKT-000001", "status": "new"})
    pipeline.save_ticket({"ticket_id": "TKT-000002", "status": "new"})
    pipeline.save_ticket({"ticket_id": "TKT-000001", "status": "assigned"})
    assert [(t["ticket_id"], t["status"]) for t in pipeline.load_tickets()] == [
        ("TKT-000001", "assigned"), ("TKT-000002", "new")]


def test_ticket_ids_count_up_from_the_highest():
    assert pipeline.next_ticket_id([]) == "TKT-000001"
    assert pipeline.next_ticket_id([{"ticket_id": "TKT-000009"}, {"ticket_id": "odd"}]) == "TKT-000010"


@pytest.fixture
def flow(store, tmp_path, monkeypatch):
    """Temporary tickets file, outbox and decision log for end-to-end tests."""
    from governance import logger
    from workflow import fallbacks
    outbox, log = tmp_path / "outbox", tmp_path / "decisions.csv"
    monkeypatch.setattr(fallbacks, "OUTBOX_DIR", outbox)
    monkeypatch.setattr(logger, "LOG_FILE", log)
    monkeypatch.delenv("REPORT_RADAR_LOGGING", raising=False)
    return {"tickets": store, "outbox": outbox, "log": log}


NOW = "2026-11-03T08:00:00+02:00"


def emails(outbox):
    return sorted(p.name.split("-", 2)[-1] for p in outbox.glob("*.eml"))


def test_urgent_report_waits_for_a_supervisor(flow):
    ticket = pipeline.process_report("Live wires hanging low across the road", "Tsutsumani", now=NOW)
    assert ticket["category"] == "electricity" and int(ticket["urgency"]) == 5
    assert (ticket["status"], ticket["approval_status"]) == ("awaiting_approval", "pending")
    assert ticket["assigned_team"] == "Electricity team" and ticket["due_by"] == "2026-11-04T08:00:00+02:00"
    assert emails(flow["outbox"]) == ["TKT-000001-approval_needed.eml"]


def test_minor_report_goes_straight_to_the_team(flow):
    ticket = pipeline.process_report("Speed hump broken and sticking out", "Old Alexandra", now=NOW)
    assert (ticket["status"], ticket["approval_status"]) == ("assigned", "not_required")
    assert emails(flow["outbox"]) == ["TKT-000001-assigned.eml"]
    assert pipeline.load_tickets()[0]["ticket_id"] == "TKT-000001"


def test_personal_details_never_reach_the_ticket_log_or_outbox(flow):
    pipeline.process_report("No water. Call Mrs Dlamini on 082 123 4567, ID 9001015009087",
                            "East Bank", resident_email="dlamini@example.com", now=NOW)
    assert emails(flow["outbox"]) == ["TKT-000001-assigned.eml", "TKT-000001-received.eml"]
    saved = [flow["tickets"].read_text(), flow["log"].read_text()]
    saved += [p.read_text() for p in flow["outbox"].glob("*.eml")]
    for secret in ("082 123 4567", "9001015009087", "Dlamini", "dlamini@example.com"):
        assert not any(secret in text for text in saved), secret
    assert pipeline.load_tickets()[0]["resident_contact"] == "yes"


def test_decision_log_names_the_stand_ins_in_use(flow):
    pipeline.process_report("No water since this morning", "Setswetla", now=NOW)
    row = flow["log"].read_text().splitlines()[-1]
    assert ",workflow,TKT-000001," in row and "stand-ins used:" not in row


def test_a_failed_step_still_saves_the_ticket_for_the_supervisor(flow, monkeypatch):
    def broken_route(ticket):
        raise KeyError("no such team")
    monkeypatch.setattr(pipeline, "step", lambda module, name: (
        (broken_route, False) if module == "routing" else (getattr(pipeline.fallbacks, name), True)))
    ticket = pipeline.process_report("Pothole on 4th Avenue", "Pan Africa", now=NOW)
    assert (ticket["status"], ticket["approval_status"]) == ("awaiting_approval", "pending")
    assert "route step" in ticket["decision_note"] and ticket["assigned_team"] == "Intake desk"
    assert pipeline.load_tickets()[0]["ticket_id"] == "TKT-000001"
    assert emails(flow["outbox"]) == ["TKT-000001-approval_needed.eml"]
    assert "route step failed: KeyError" in flow["log"].read_text()


def test_inbox_is_processed_once_even_if_run_twice(flow, tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "PROCESSED_FILE", tmp_path / "processed.csv")
    first = pipeline.process_inbox(pipeline.INBOX_EXAMPLE, now=NOW)
    second = pipeline.process_inbox(pipeline.INBOX_EXAMPLE, now=NOW)
    assert len(first["new"]) == 10 and first["skipped"] == []
    assert second["new"] == [] and len(second["skipped"]) == 10
    assert [t["ticket_id"] for t in pipeline.load_tickets()] == [f"TKT-{i:06d}" for i in range(1, 11)]


def test_inbox_rows_without_a_description_are_skipped(flow, tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "PROCESSED_FILE", tmp_path / "processed.csv")
    inbox = tmp_path / "inbox.csv"
    inbox.write_text("report_ref,description,ward,resident_email\nA1,,Tsutsumani,\nA2,Pothole,East Bank,\n")
    summary = pipeline.process_inbox(inbox, now=NOW)
    assert summary["invalid"] == ["line 2"] and len(summary["new"]) == 1


def test_overdue_tickets_are_escalated_and_the_supervisor_emailed(flow):
    late = pipeline.process_report("Speed hump broken and sticking out", "Tsutsumani", now=NOW)
    pipeline.process_report("Live wires hanging low across the road", "East Bank", now=NOW)  # waits for approval
    nine_days_later = "2026-11-12T08:00:00+02:00"  # urgency 2 has 7 days
    escalated = pipeline.check_overdue(now=nine_days_later)
    assert [t["ticket_id"] for t in escalated] == [late["ticket_id"]]
    saved = {t["ticket_id"]: t["status"] for t in pipeline.load_tickets()}
    assert saved == {"TKT-000001": "escalated", "TKT-000002": "awaiting_approval"}
    assert "TKT-000001-overdue.eml" in emails(flow["outbox"])
    assert pipeline.check_overdue(now=nine_days_later) == []  # already escalated: nothing new


def test_demo_runs_and_can_be_repeated(flow, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(pipeline, "PROCESSED_FILE", tmp_path / "processed.csv")
    assert pipeline.main(["--demo"]) == 0
    assert pipeline.main(["--demo"]) == 0
    assert len(pipeline.load_tickets()) == 10
    assert "0 new, 10 already processed" in capsys.readouterr().out
