"""Assign a team, depot, and urgency-based deadline to a ticket."""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path

from governance.logger import log_decision

# Team assumption: these service-level targets have not yet been measured.
# Deadlines depend on urgency, not ward or report volume. Week 6 found that
# urgent reports already wait 44 hours in Tsutsumani versus 24 in Old Alexandra.
SLA_HOURS = {5: 24, 4: 48, 3: 72, 2: 168, 1: 336}


def _read_rules(filename: str, key: str, value: str) -> dict[str, str]:
    path = Path(__file__).resolve().parent / filename
    with path.open(newline="", encoding="utf-8") as handle:
        return {row[key].strip(): row[value].strip() for row in csv.DictReader(handle)}


ROUTING_RULES = _read_rules("routing_rules.csv", "category", "team")
DEPOTS = _read_rules("depots.csv", "ward", "depot")


def route(ticket: dict) -> dict:
    """Return a routed copy of a ticket and log the routing decision."""
    routed = ticket.copy()
    category = ticket.get("category", "")
    ward = ticket.get("ward", "")
    team = ROUTING_RULES.get(category, "Intake desk")
    depot = DEPOTS.get(ward, "Central depot")
    sla_hours = SLA_HOURS[int(ticket["urgency"])]
    due_by = (datetime.fromisoformat(ticket["received_at"])
              + timedelta(hours=sla_hours)).isoformat(timespec="seconds")

    routed.update(assigned_team=team, depot=depot, sla_hours=sla_hours, due_by=due_by)
    log_decision(
        "routing",
        ticket.get("ticket_id"),
        ticket.get("description_masked", ""),
        f"team={team}; depot={depot}; due_by={due_by}",
        ticket.get("reason", ""),
    )
    return routed