"""Tests for the weekly summary for managers."""
from datetime import date, datetime, timezone

import pandas as pd

from weekly_summary import (ALL_TEAMS, build_summary, latest_full_week, next_week_forecast,
                            summarise_week, team_categories, ticket_counts)

TEAMS = {"Water": ["water"], "Electricity": ["electricity", "streetlights"]}
NOW = datetime(2026, 11, 10, 9, 0, tzinfo=timezone.utc)


def report(day, category, urgency=3, status="resolved", hours=10.0, ward="East Bank"):
    return {"timestamp": pd.Timestamp(day), "category": category, "urgency": urgency,
            "status": status, "hours_to_resolve": hours, "ward_or_suburb": ward,
            "review_required": False}


def sample():
    return pd.DataFrame([
        # week before: Mon 5 Oct to Sun 11 Oct 2026
        report("2026-10-05 08:00", "water"),
        report("2026-10-07 08:00", "electricity"),
        # summary week: Mon 12 Oct to Sun 18 Oct 2026
        report("2026-10-12 09:00", "water", urgency=5, status="open", ward="Old Alexandra"),
        report("2026-10-13 09:00", "water", hours=20.0, ward="Old Alexandra"),
        report("2026-10-14 09:00", "streetlights", urgency=4, hours=30.0),
        report("2026-10-18 23:00", "electricity", status="in_progress"),
        # incomplete week (data ends on a Wednesday)
        report("2026-10-21 09:00", "water"),
    ])


def test_the_last_complete_week_is_used():
    assert latest_full_week(sample()["timestamp"]) == date(2026, 10, 12)
    assert latest_full_week(pd.Series([pd.Timestamp("2026-10-18 10:00")])) == date(2026, 10, 12)


def test_week_figures_for_all_teams():
    s = summarise_week(sample(), date(2026, 10, 12))
    assert (s["reports"], s["last_week"], s["urgent"], s["not_fixed"], s["urgent_not_fixed"]) == (4, 2, 2, 2, 1)
    assert s["median_hours_to_fix"] == 25.0  # fixed reports took 20 and 30 hours
    assert s["by_type"].loc["water"].tolist() == [2, 1]
    assert s["areas"].to_dict() == {"Old Alexandra": 2, "East Bank": 2}


def test_one_team_only_counts_its_own_problem_types():
    s = summarise_week(sample(), date(2026, 10, 12), TEAMS["Electricity"])
    assert (s["reports"], s["last_week"], s["urgent"]) == (2, 1, 1)
    assert set(s["by_type"].index) == {"electricity", "streetlights"}


def test_all_teams_forecast_matches_the_overview_and_a_team_sums_its_types():
    by_cat = pd.DataFrame({"category": ["water", "electricity", "streetlights", "water"],
                           "week_start": ["2026-10-19"] * 3 + ["2026-10-12"],
                           "forecast": [17.6, 10.0, 3.0, 99.0]})
    projected = pd.DataFrame({"week_start": ["2026-10-19", "Total next 4 weeks"],
                              "expected_reports": [69, 276]})
    assert next_week_forecast(date(2026, 10, 12), by_cat, None, projected) == 69
    assert next_week_forecast(date(2026, 10, 12), by_cat, ["electricity", "streetlights"]) == 13.0
    assert next_week_forecast(date(2026, 10, 12), None, ["water"]) is None


def test_ticket_counts_for_one_team():
    tickets = [
        {"assigned_team": "Water", "status": "assigned", "due_by": "2026-11-09T08:00:00+00:00"},
        {"assigned_team": "Water", "status": "awaiting_approval", "due_by": "2026-11-12T08:00:00+00:00"},
        {"assigned_team": "Water", "status": "resolved", "due_by": "2026-11-01T08:00:00+00:00"},
        {"assigned_team": "Roads", "status": "assigned", "due_by": "2026-11-01T08:00:00+00:00"},
    ]
    assert ticket_counts(tickets, "Water", NOW) == {"open": 2, "awaiting_approval": 1, "overdue": 1}
    assert ticket_counts(tickets, None, NOW)["overdue"] == 2
    assert ticket_counts([], None, NOW) is None


def test_summary_reads_plainly_and_names_the_week_and_team():
    text = build_summary(sample(), "Water", teams=TEAMS, now=NOW)
    assert text.startswith("# Report Radar weekly summary: Water")
    assert "**Week:** 12 Oct 2026 to 18 Oct 2026" in text
    assert "**2 reports** this week (+100% on the week before, 1)" in text
    assert "1. Old Alexandra: 2 reports" in text
    assert "synthetic" in text
    assert "Electricity" not in text.split("## By type of problem")[1]


def test_all_teams_summary_includes_live_tickets_when_there_are_some():
    tickets = [{"assigned_team": "Water", "status": "awaiting_approval", "due_by": ""}]
    text = build_summary(sample(), ALL_TEAMS, teams=TEAMS, tickets=tickets, now=NOW)
    assert "1 open, 1 waiting for a supervisor, 0 past their deadline" in text
    assert "## Workflow tickets" not in build_summary(sample(), ALL_TEAMS, teams=TEAMS, now=NOW)


def test_teams_come_from_the_routing_rules():
    teams = team_categories()
    assert teams["Electricity"] == ["electricity", "streetlights"]
    assert teams["Waste"] == ["refuse"]
