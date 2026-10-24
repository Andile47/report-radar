"""Capacity planner: "Do we have enough crews?"

plan() is plain arithmetic, so it can be tested without Streamlit.
show_capacity_planner() draws the section at the bottom of the Workload forecast tab.
"""
from __future__ import annotations

import math
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
WORKLOAD_FILE = ROOT / "forecast" / "projected_workload.csv"
REPORTS_FILE = ROOT / "data" / "reports.csv"

COLOR_EXPECTED = "#2c5282"  # dark blue: reports expected
COLOR_CAPACITY = "#dd6b20"  # orange: what the crews can fix


def plan(crews: int, per_crew: int, expected_per_week: list[float], unfixed_now: int) -> dict:
    """Simple capacity arithmetic.

    crews              number of crews
    per_crew           reports one crew fixes in a week
    expected_per_week  expected reports for each of the next weeks (a list)
    unfixed_now        reports not fixed yet today
    """
    if per_crew <= 0:
        raise ValueError("per_crew must be more than 0")
    if crews < 0:
        raise ValueError("crews cannot be negative")
    if not expected_per_week:
        raise ValueError("expected_per_week cannot be empty")

    capacity = crews * per_crew                                   # reports fixed per week
    gaps = [capacity - e for e in expected_per_week]              # + = spare, - = short
    expected_avg = sum(expected_per_week) / len(expected_per_week)
    unfixed_after = max(0, unfixed_now - sum(gaps))               # never below 0
    crews_needed = math.ceil(round(expected_avg / per_crew, 6))   # round up
    return {
        "capacity": capacity,
        "expected_avg": expected_avg,
        "gaps": gaps,
        "gap_avg": sum(gaps) / len(gaps),
        "unfixed_after": unfixed_after,
        "crews_needed": crews_needed,
        "covered": all(g >= 0 for g in gaps),
    }


def fixed_per_week(reports: pd.DataFrame) -> tuple[float, float] | None:
    """Reports fixed per week, counted by the week they were fixed
    (timestamp + hours_to_resolve). Returns (whole period, last 8 weeks)."""
    done = reports[(reports["status"] == "resolved") & reports["hours_to_resolve"].notna()].copy()
    if done.empty:
        return None
    fixed_at = pd.to_datetime(done["timestamp"]) + pd.to_timedelta(done["hours_to_resolve"], unit="h")
    weekly = fixed_at.dt.to_period("W-SUN").value_counts().sort_index()
    weekly = weekly.reindex(pd.period_range(weekly.index.min(), weekly.index.max(), freq="W-SUN"),
                            fill_value=0)
    weekly = weekly.iloc[1:-1]  # drop the first and last weeks: they are only part-weeks
    if weekly.empty:
        return None
    return float(weekly.mean()), float(weekly.tail(8).mean())


def show_capacity_planner() -> None:
    st.divider()
    st.subheader("Do we have enough crews?")

    if not WORKLOAD_FILE.exists():
        st.info("The workload forecast isn't built yet. Run `python run_all.py` first.")
        return
    workload = pd.read_csv(WORKLOAD_FILE)
    weeks = workload.iloc[:-1]  # the last row is the 4-week total
    if weeks.empty:
        st.info("The workload forecast has no weekly rows yet.")
        return

    reports = pd.read_csv(REPORTS_FILE, parse_dates=["timestamp"]) if REPORTS_FILE.exists() else None
    unfixed_now = int((reports["status"] != "resolved").sum()) if reports is not None else 0

    col1, col2 = st.columns(2)
    crews = col1.number_input("Number of crews", min_value=0, value=5, step=1)
    per_crew = col2.number_input("Reports one crew fixes in a week", min_value=0, value=14, step=1)
    mode = st.radio("Plan for", ["A normal month", "A busy month"], horizontal=True,
                    help="A busy month uses the top of the likely range.")

    if crews < 1 or per_crew < 1:
        st.info("Enter at least 1 crew and at least 1 report per crew to see the answer.")
        return

    column = "expected_reports" if mode == "A normal month" else "likely_high"
    expected = [float(v) for v in weeks[column]]
    result = plan(int(crews), int(per_crew), expected, unfixed_now)

    cap = result["capacity"]
    exp = round(result["expected_avg"])
    last_day = pd.to_datetime(weeks["week_start"]).max() + pd.Timedelta(days=6)
    by_date = f"{last_day.day} {last_day:%b}"
    if result["covered"]:
        spare = round(result["gap_avg"])
        st.success(f"{crews} crews can fix about {cap} reports a week. "
                   f"That covers the {exp} expected, with about {spare} to spare.")
        if unfixed_now:
            st.caption(f"The {unfixed_now:,} reports not fixed yet would fall to about "
                       f"{result['unfixed_after']:,} by {by_date}.")
    else:
        short = round(-result["gap_avg"])
        st.error(f"{crews} crews can fix about {cap} a week, {short} short of the {exp} expected. "
                 f"Unfixed reports will grow from about {unfixed_now:,} to about "
                 f"{result['unfixed_after']:,} by {by_date}. "
                 f"You need {result['crews_needed']} crews.")

    chart_data = pd.DataFrame({
        "Week starting": [f"{pd.Timestamp(w).day} {pd.Timestamp(w):%b}" for w in weeks["week_start"]],
        "Reports expected": expected,
        "Reports the crews can fix": [cap] * len(expected),
    }).melt("Week starting", var_name="Series", value_name="Reports")
    order = list(dict.fromkeys(chart_data["Week starting"]))
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("Week starting:N", sort=order, title=None, axis=alt.Axis(labelAngle=0)),
        xOffset="Series:N",
        y=alt.Y("Reports:Q", title="Reports per week"),
        color=alt.Color("Series:N", title=None,
                        scale=alt.Scale(domain=["Reports expected", "Reports the crews can fix"],
                                        range=[COLOR_EXPECTED, COLOR_CAPACITY]),
                        legend=alt.Legend(orient="top")),
        tooltip=["Week starting", "Series", alt.Tooltip("Reports:Q", format=".0f")],
    ).properties(height=240)
    st.altair_chart(chart, width="stretch")

    if reports is not None:
        past = fixed_per_week(reports)
        if past:
            st.caption(f"Reality check: last year the teams fixed about {past[0]:.0f} reports a week "
                       f"(about {past[1]:.0f} a week over the last 8 weeks).")
    st.caption("Assumes every report takes about the same effort, and any crew can fix any problem type.")
