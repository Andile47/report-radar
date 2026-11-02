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
