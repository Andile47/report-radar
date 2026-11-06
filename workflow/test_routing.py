"""Tests for urgency-based workflow routing. Run with: pytest workflow/test_routing.py"""
from datetime import datetime, timedelta
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
    ("water", "Water"),
    ("sanitation", "Sanitation"),
    ("electricity", "Electricity"),
    ("streetlights", "Electricity"),
    ("roads", "Roads"),
    ("refuse", "Waste"),
    ("other", "Intake desk"),
])
def test_categories_route_to_their_teams(category, team):
    ticket = {"category": category, "ward": "Old Alexandra", "urgency": 3,
              "received_at": "2026-11-03T08:15:00"}
    assert routing.route(ticket)["assigned_team"] == team


def test_unknown_category_and_ward_use_safe_defaults():
    ticket = {"category": "unknown service", "ward": "Unknown ward", "urgency": 3,
              "received_at": "2026-11-03T08:15:00"}
    routed = routing.route(ticket)
    assert routed["assigned_team"] == "Intake desk"
    assert routed["depot"] == "Central depot"


@pytest.mark.parametrize("urgency,sla_hours", [(5, 24), (4, 48), (3, 72), (2, 168), (1, 336)])
def test_due_by_uses_the_sla_for_each_urgency(urgency, sla_hours):
    ticket = {"category": "water", "ward": "Old Alexandra", "urgency": urgency,
              "received_at": "2026-11-03T08:15:00"}
    routed = routing.route(ticket)
    expected = (datetime.fromisoformat(ticket["received_at"])
                + timedelta(hours=sla_hours)).isoformat(timespec="seconds")
    assert routed["sla_hours"] == sla_hours
    assert routed["due_by"] == expected


def test_urgent_tickets_in_different_wards_get_the_same_deadline():
    common = {"category": "water", "urgency": 5, "received_at": "2026-11-03T08:15:00"}
    old_alexandra = routing.route({**common, "ward": "Old Alexandra"})
    tsutsumani = routing.route({**common, "ward": "Tsutsumani"})
    assert old_alexandra["due_by"] == tsutsumani["due_by"]


def test_route_returns_a_new_ticket_without_changing_the_input(monkeypatch):
    ticket = {"ticket_id": "TKT-TEST-01", "description_masked": "Made-up pipe leak report",
              "category": "water", "ward": "East Bank", "urgency": 4,
              "received_at": "2026-11-03T08:15:00", "reason": "made-up test reason"}
    original = ticket.copy()
    logged = []
    monkeypatch.setattr(routing, "log_decision", lambda *args: logged.append(args))

    routed = routing.route(ticket)

    assert routed is not ticket
    assert ticket == original
    assert routed["assigned_team"] == "Water"
    assert routed["depot"] == "East depot"
    assert logged == [(
        "routing", "TKT-TEST-01", "Made-up pipe leak report",
        f"team=Water; depot=East depot; due_by={routed['due_by']}",
        "made-up test reason",
    )]


def test_every_routed_team_is_one_of_the_agreed_teams_with_an_email_address():
    from workflow import fallbacks
    agreed = {"Water", "Sanitation", "Electricity", "Roads", "Waste", "Intake desk"}
    assert set(routing.ROUTING_RULES.values()) <= agreed
    for team in set(routing.ROUTING_RULES.values()) - {"Intake desk"}:
        assert team in fallbacks.TEAM_ADDRESSES, team
