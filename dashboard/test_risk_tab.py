"""Tests for the risk report. They don't need Streamlit running.

Run with:  pytest dashboard
"""
from datetime import date

import pandas as pd

from risk_tab import (REGISTER_COLUMNS, build_risk_report, fairness_findings,
                      language_findings, latest_decisions, load_register,
                      register_problems, summarise)

TODAY = date(2026, 11, 2)


def sample_file(tmp_path, rows):
    """Write a small risk register CSV and return its path."""
    path = tmp_path / "risk_register.csv"
    pd.DataFrame(rows, columns=REGISTER_COLUMNS).to_csv(path, index=False)
    return path


def row(risk_id, likelihood, impact, status="Open", owner="Role 1", risk="A risk", score=None):
    return [risk_id, risk, "Fairness", "Residents", likelihood, impact,
            likelihood * impact if score is None else score,
            "Some evidence", "Some fix", owner, status]


# ---------- the report with an empty register ----------
def test_report_works_with_a_missing_register(tmp_path):
    register = load_register(tmp_path / "does_not_exist.csv")
    report = build_risk_report(register, today=TODAY)
    assert "# Risk evaluation report" in report
    assert "2 November 2026" in report
    assert "No risks have been logged yet" in report
    assert "What we can't fix yet" in report  # this section never disappears


def test_report_works_with_a_header_only_register(tmp_path):
    path = sample_file(tmp_path, [])
    report = build_risk_report(load_register(path), today=TODAY)
    assert "No risks have been logged yet" in report


# ---------- the report with sample rows ----------
def test_report_lists_risks_highest_score_first(tmp_path):
    path = sample_file(tmp_path, [row("R1-01", 2, 2, risk="Small risk"),
                                  row("R1-02", 5, 4, risk="Big risk")])
    report = build_risk_report(load_register(path), today=TODAY)
    assert "We are tracking 2 risks" in report
    assert "1 is high" in report
    assert report.index("Big risk") < report.index("Small risk")


def test_report_has_the_columns_a_manager_asked_for(tmp_path):
    report = build_risk_report(load_register(sample_file(tmp_path, [row("R1-01", 4, 4)])),
                               today=TODAY)
    for heading in ["Who is harmed", "Evidence", "Mitigation", "Owner", "Status"]:
        assert heading in report


def test_report_says_when_teammate_files_are_missing(tmp_path):
    report = build_risk_report(load_register(sample_file(tmp_path, [row("R1-01", 4, 4)])),
                               fairness=None, language=None, today=TODAY)
    assert "have not been added yet" in report


def test_pipe_characters_do_not_break_the_table(tmp_path):
    path = sample_file(tmp_path, [row("R1-01", 3, 3, risk="Bad | pipe")])
    assert "Bad \\| pipe" in build_risk_report(load_register(path), today=TODAY)


def test_only_the_top_five_risks_are_in_the_table(tmp_path):
    rows = [row(f"R1-0{i}", 3, 3, risk=f"Risk number {i}") for i in range(1, 8)]
    report = build_risk_report(load_register(sample_file(tmp_path, rows)), today=TODAY, top_n=5)
    assert report.count("| Role 1 |") == 5


# ---------- loading and counting ----------
def test_score_is_always_likelihood_times_impact(tmp_path):
    path = sample_file(tmp_path, [row("R1-01", 4, 4, score=99)])
    register = load_register(path)
    assert register["score"].iloc[0] == 16
    assert any("99" in note for note in register_problems(register))


def test_bad_ratings_do_not_crash(tmp_path):
    path = tmp_path / "risk_register.csv"
    path.write_text(",".join(REGISTER_COLUMNS) + "\nR1-01,Odd,Fairness,Residents,7,x,,e,m,Role 1,Open\n")
    register = load_register(path)
    assert register["score"].iloc[0] == 0
    assert register_problems(register)


def test_mitigated_and_closed_risks_are_not_counted_as_open(tmp_path):
    rows = [row("R1-01", 5, 5, status="Mitigated"), row("R1-02", 5, 5, status="closed"),
            row("R1-03", 5, 5, status="In progress"), row("R1-04", 1, 1, status="Open")]
    summary = summarise(load_register(sample_file(tmp_path, rows)))
    assert summary["total"] == 4
    assert summary["high"] == 3
    assert summary["still_open"] == 2


# ---------- teammates' files ----------
def test_fairness_findings_handle_missing_and_real_tables():
    assert "not been added yet" in fairness_findings(None)[0]
    table = pd.DataFrame({"ward": ["Old Alexandra", "Tsutsumani"],
                          "median_hours_urgent": [24.0, 44.0],
                          "breaks_rule": [False, True]})
    text = " ".join(fairness_findings(table))
    assert "Tsutsumani" in text and "1.8 times" in text
    assert "break our fairness rule: Tsutsumani" in text


def test_fairness_findings_do_not_crash_on_unknown_columns():
    assert fairness_findings(pd.DataFrame({"x": [1, 2]}))


def test_language_findings_handle_missing_and_real_tables():
    assert "not been added yet" in language_findings(None)[0]
    table = pd.DataFrame({"language": ["English", "Sesotho"], "category_accuracy": [0.9, 0.5]})
    text = language_findings(table)[0]
    assert "least accurate in Sesotho (50%)" in text and "40 percentage points" in text


def test_latest_decisions_returns_newest_20_first():
    log = pd.DataFrame({"timestamp": pd.date_range("2026-10-01", periods=30, freq="h").astype(str),
                        "report_id": [f"R{i}" for i in range(30)]})
    newest = latest_decisions(log, 20)
    assert len(newest) == 20
    assert newest["report_id"].iloc[0] == "R29"
