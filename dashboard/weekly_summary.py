"""Weekly summary for managers: one week of reports for all teams or one team
(department), as a short report they can download from the Overview tab.

The building blocks are plain Python (no Streamlit), so they can be tested;
show_weekly_summary() draws the picker, preview and download button.
"""
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ROUTING_RULES = ROOT / "workflow" / "routing_rules.csv"
PROJECTED_FILE = ROOT / "forecast" / "projected_workload.csv"  # the overall forecast on the Overview
ALL_TEAMS = "All teams"
OPEN_STATUSES = ("open", "in_progress", "escalated")
CLOSED_TICKETS = ("resolved", "rejected")
PROBLEM_NAMES = {"water": "Water", "electricity": "Electricity", "roads": "Roads",
                 "sanitation": "Sewage & toilets", "refuse": "Rubbish",
                 "streetlights": "Streetlights", "other": "Unclear - needs checking"}


def team_categories(path: Path = ROUTING_RULES) -> dict[str, list[str]]:
    """Team -> the problem types routed to it, from the routing rules."""
    teams: dict[str, list[str]] = {}
    if not Path(path).exists():
        return teams
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            teams.setdefault(row["team"].strip(), []).append(row["category"].strip())
    return teams


def latest_full_week(timestamps: pd.Series) -> date:
    """The Monday of the last complete Monday-to-Sunday week in the data."""
    last = pd.to_datetime(timestamps).max().date()
    monday = last - timedelta(days=last.weekday())
    return monday if last.weekday() == 6 else monday - timedelta(days=7)


def _week(reports: pd.DataFrame, start: date) -> pd.DataFrame:
    stamps = pd.to_datetime(reports["timestamp"])
    begin = pd.Timestamp(start)
    return reports[(stamps >= begin) & (stamps < begin + pd.Timedelta(days=7))]


def _change(now: int, before: int) -> str:
    if before == 0:
        return "new" if now else "no change"
    pct = round((now - before) / before * 100)
    return "no change" if pct == 0 else f"{pct:+d}%"


def _day(value: date) -> str:
    return f"{value.day} {value:%b %Y}"


def summarise_week(reports: pd.DataFrame, week_start: date,
                   categories: list[str] | None = None) -> dict:
    """The week's figures, and the week before's for comparison.
    categories: only these problem types (one team); None means all."""
    if categories is not None:
        reports = reports[reports["category"].isin(categories)]
    this, last = _week(reports, week_start), _week(reports, week_start - timedelta(days=7))
    fixed = this[this["status"] == "resolved"]["hours_to_resolve"].dropna()
    by_type = pd.DataFrame({
        "this_week": this["category"].value_counts(),
        "last_week": last["category"].value_counts(),
    }).fillna(0).astype(int).sort_values("this_week", ascending=False)
    return {
        "week_start": week_start,
        "reports": len(this),
        "last_week": len(last),
        "urgent": int((this["urgency"] >= 4).sum()),
        "not_fixed": int(this["status"].isin(OPEN_STATUSES).sum()),
        "urgent_not_fixed": int(((this["urgency"] >= 4) & this["status"].isin(OPEN_STATUSES)).sum()),
        "need_checking": int(this["review_required"].astype(bool).sum()) if "review_required" in this else 0,
        "median_hours_to_fix": float(fixed.median()) if len(fixed) else None,
        "by_type": by_type,
        "areas": this["ward_or_suburb"].value_counts().head(3),
    }


def next_week_forecast(week_start: date, by_category: pd.DataFrame | None,
                       categories: list[str] | None, projected: pd.DataFrame | None = None) -> float | None:
    """Forecast reports for the week after week_start. For all teams this is the
    overall forecast (the same figure as the Overview); for one team, the sum of
    its problem types' forecasts."""
    nxt = pd.Timestamp(week_start + timedelta(days=7))
    if categories is None and projected is not None:
        weeks = pd.to_datetime(projected["week_start"], errors="coerce")
        row = projected[weeks == nxt]
        if len(row):
            return float(row["expected_reports"].iloc[0])
    if by_category is None or by_category.empty:
        return None
    rows = by_category[pd.to_datetime(by_category["week_start"]) == nxt]
    if categories is not None:
        rows = rows[rows["category"].isin(categories)]
    rows = rows.dropna(subset=["forecast"])
    return float(rows["forecast"].sum()) if len(rows) else None


def ticket_counts(tickets: list[dict] | None, team: str | None, now: datetime) -> dict | None:
    """Live workflow tickets: open, waiting for a supervisor, and overdue."""
    if not tickets:
        return None
    if team:
        tickets = [t for t in tickets if t.get("assigned_team") == team]
    open_tickets = [t for t in tickets if t.get("status") not in CLOSED_TICKETS]

    def overdue(ticket):
        try:
            return (ticket.get("status") in ("assigned", "in_progress", "escalated")
                    and datetime.fromisoformat(ticket["due_by"]) < now)
        except (KeyError, TypeError, ValueError):
            return False

    return {"open": len(open_tickets),
            "awaiting_approval": sum(t.get("status") == "awaiting_approval" for t in tickets),
            "overdue": sum(overdue(t) for t in open_tickets)}


def build_summary(reports: pd.DataFrame, team: str = ALL_TEAMS, week_start: date | None = None,
                  by_category: pd.DataFrame | None = None, tickets: list[dict] | None = None,
                  teams: dict[str, list[str]] | None = None, now: datetime | None = None,
                  projected: pd.DataFrame | None = None) -> str:
    """The weekly summary as Markdown, ready to download or preview."""
    now = now or datetime.now().astimezone()
    teams = teams if teams is not None else team_categories()
    categories = None if team == ALL_TEAMS else teams.get(team, [])
    week_start = week_start or latest_full_week(reports["timestamp"])
    s = summarise_week(reports, week_start, categories)
    week_end = week_start + timedelta(days=6)

    lines = [f"# Report Radar weekly summary: {team}", "",
             f"**Week:** {_day(week_start)} to {_day(week_end)}  ",
             f"**Prepared:** {_day(now.date())}  ",
             "**Data:** synthetic (realistic but made-up) reports for Alexandra, Johannesburg", ""]
    if team != ALL_TEAMS:
        kinds = ", ".join(PROBLEM_NAMES.get(c, c) for c in categories) or "none"
        lines += [f"Covers the problem types routed to the {team} team: {kinds}.", ""]

    lines += ["## At a glance", ""]
    lines.append(f"- **{s['reports']} reports** this week ({_change(s['reports'], s['last_week'])} "
                 f"on the week before, {s['last_week']}).")
    lines.append(f"- **{s['urgent']} urgent** (urgency 4 or 5); "
                 f"{s['urgent_not_fixed']} of them are not fixed yet.")
    lines.append(f"- **{s['not_fixed']} not fixed yet** of this week's reports.")
    if s["median_hours_to_fix"] is not None:
        lines.append(f"- Reports fixed this week took a median of **{s['median_hours_to_fix']:.0f} hours**.")
    if s["need_checking"]:
        lines.append(f"- **{s['need_checking']}** were too unclear to sort automatically and need a person to check.")
    forecast = next_week_forecast(week_start, by_category, categories, projected)
    if forecast is not None:
        lines.append(f"- **About {forecast:.0f} reports** are expected next week (forecast).")
    lines.append("")

    if len(s["by_type"]):
        lines += ["## By type of problem", "", "| Problem | This week | Week before | Change |",
                  "| --- | ---: | ---: | --- |"]
        for code, row in s["by_type"].iterrows():
            lines.append(f"| {PROBLEM_NAMES.get(code, code)} | {row['this_week']} | {row['last_week']} | "
                         f"{_change(row['this_week'], row['last_week'])} |")
        lines.append("")

    if len(s["areas"]):
        lines += ["## Busiest areas", ""]
        lines += [f"{n}. {area}: {count} report{'s' if count != 1 else ''}" for n, (area, count) in enumerate(s["areas"].items(), 1)]
        lines.append("")

    counts = ticket_counts(tickets, None if team == ALL_TEAMS else team, now)
    if counts is not None:
        lines += ["## Workflow tickets right now", "",
                  f"- {counts['open']} open, {counts['awaiting_approval']} waiting for a supervisor, "
                  f"{counts['overdue']} past their deadline.", ""]

    lines += ["## How these figures are made", "",
              "Counts come from the reports received in the week, sorted by Report Radar's classifier. "
              "\"Not fixed yet\" means not resolved by the end of the data. The forecast comes from the "
              "Forecast tab. Workflow tickets are the live tickets on the Workflow tab."]
    return "\n".join(lines) + "\n"


def show_weekly_summary(reports: pd.DataFrame, by_category: pd.DataFrame | None = None) -> None:
    """Overview tab section: pick a team, preview the summary, download it."""
    import streamlit as st

    teams = team_categories()
    choices = [ALL_TEAMS] + [t for t in teams if t != "Intake desk"]
    team = st.selectbox("Team (department)", choices, key="weekly_summary_team")
    tickets = None
    try:
        from workflow.pipeline import load_tickets
        tickets = load_tickets()
    except Exception:  # the summary still works without live tickets
        tickets = None
    projected = pd.read_csv(PROJECTED_FILE) if PROJECTED_FILE.exists() else None
    text = build_summary(reports, team, by_category=by_category, tickets=tickets, teams=teams,
                         projected=projected)
    st.download_button("Download the weekly summary", data=text,
                       file_name=f"report_radar_weekly_{team.lower().replace(' ', '_')}.md",
                       mime="text/markdown", key="weekly_summary_download")
    with st.expander("Preview the summary"):
        st.markdown(text)
