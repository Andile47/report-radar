"""Tests for the decision log. Run from the repo root:  pytest governance"""
import csv
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "intake"))
from governance import logger  # noqa: E402
import classifier  # noqa: E402


@pytest.fixture
def log_file(tmp_path, monkeypatch):
    """Point the logger at a temporary file and make sure logging is on."""
    path = tmp_path / "decisions.csv"
    monkeypatch.setattr(logger, "LOG_FILE", path)
    monkeypatch.delenv("REPORT_RADAR_LOGGING", raising=False)
    return path


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_row_has_the_agreed_columns(log_file):
    logger.log_decision("classifier", "ALX-1", "No water since this morning",
                        "category=water", "water: no water")
    rows = read_rows(log_file)
    assert len(rows) == 1
    assert list(rows[0]) == logger.COLUMNS
    assert rows[0]["rules_version"] == logger.RULES_VERSION["classifier"]


def test_rows_are_appended_with_one_header(log_file):
    logger.log_decision("classifier", "A", "x", "y", "z")
    logger.log_decision("forecast", "", "x", "y", "z")
    assert log_file.read_text().count("timestamp,component") == 1
    assert [r["component"] for r in read_rows(log_file)] == ["classifier", "forecast"]


def test_personal_information_is_masked(log_file):
    logger.log_decision("classifier", "A",
                        "Call 082 123 4567 or me@example.com, ID 9001015009087", "y", "z")
    summary = read_rows(log_file)[0]["input_summary"]
    assert "082" not in summary and "example.com" not in summary and "9001015009087" not in summary
    assert "[PHONE]" in summary and "[EMAIL]" in summary and "[ID]" in summary


def test_summary_is_cut_to_80_characters():
    assert len(logger.summarise("pothole " * 40)) == logger.SUMMARY_LENGTH


def test_logging_can_be_switched_off(log_file, monkeypatch):
    monkeypatch.setenv("REPORT_RADAR_LOGGING", "off")
    assert logger.log_decision("classifier", "A", "x", "y", "z") == 0
    assert not log_file.exists()


def test_unwritable_log_does_not_crash(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("REPORT_RADAR_LOGGING", raising=False)
    folder_in_the_way = tmp_path / "decisions.csv"
    folder_in_the_way.mkdir()  # a folder where the file should be
    assert logger.log_decision("classifier", "A", "x", "y", "z", folder_in_the_way) == 0
    assert "Warning" in capsys.readouterr().out


def test_classifier_results_are_the_same_with_logging_on_or_off(tmp_path, monkeypatch):
    reports = pd.DataFrame({
        "report_id": ["T1", "T2", "T3"],
        "description": ["Burst pipe flooding 4th Avenue", "Something is wrong please come",
                        "Live wires hanging low across the road"],
    })
    source = tmp_path / "reports.csv"
    reports.to_csv(source, index=False)
    monkeypatch.setattr(logger, "LOG_FILE", tmp_path / "decisions.csv")

    monkeypatch.setenv("REPORT_RADAR_LOGGING", "on")
    with_log = classifier.process_csv(source, tmp_path / "on.csv", tmp_path / "clean_on.csv")
    monkeypatch.setenv("REPORT_RADAR_LOGGING", "off")
    without_log = classifier.process_csv(source, tmp_path / "off.csv", tmp_path / "clean_off.csv")

    pd.testing.assert_frame_equal(with_log, without_log)
    assert (tmp_path / "on.csv").read_text() == (tmp_path / "off.csv").read_text()
    logged = read_rows(tmp_path / "decisions.csv")
    assert [r["report_id"] for r in logged] == ["T1", "T2", "T3"]
    assert logged[1]["output"] == "category=other; urgency=2; needs_review=yes"
