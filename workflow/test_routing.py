"""Tests for urgency-based workflow routing. Run with: pytest workflow/test_routing.py"""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workflow import routing  # noqa: E402


@pytest.fixture(autouse=True)
def mute_routing_log(monkeypatch):
    monkeypatch.setattr(routing, "log_decision", lambda *args: None)


@pytest.mark.parametrize("category,team", [
    ("water", "Water team"),
    ("sanitation", "Sanitation team"),
    ("electricity", "Electricity team"),
    ("streetlights", "Electricity team"),
    ("roads", "Roads team"),
    ("refuse", "Waste team"),
    ("other", "Intake desk"),
])
def test_categories_route_to_their_teams(category, team):
    ticket = {"category": category, "ward": "Old Alexandra", "urgency": 3,
              "received_at": "2026-11-03T08:15:00"}
    assert routing.route(ticket)["assigned_team"] == team
