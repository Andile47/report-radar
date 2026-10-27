"""Report Radar - decision log (Week 6, Role 4: Logging and Transparency Lead).

Every time Report Radar makes a decision (sorting a report, making a
forecast), one row is added to governance/logs/decisions.csv saying what
was decided, when, why, and with which version of the rules. This lets
anyone check or challenge a decision later.

Columns (agreed with the team):
    timestamp, component, report_id, input_summary, output, reason, rules_version

Privacy: input_summary is passed through mask_personal_info() from
governance/privacy.py (Role 3) and cut to 80 characters before it is
written, so the log never holds phone numbers, ID numbers or emails.

Switch logging off with the environment variable REPORT_RADAR_LOGGING=off
(for example when running tests). Logging never changes any result: if
writing the log fails, a warning is printed and the program carries on.
"""
from __future__ import annotations

import csv
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "governance" / "logs" / "decisions.csv"
COLUMNS = ["timestamp", "component", "report_id", "input_summary",
           "output", "reason", "rules_version"]
SUMMARY_LENGTH = 80

# Change the version whenever a component's rules or model change, so each
# logged decision can be traced to the rules that made it.
RULES_VERSION = {
    "classifier": "classifier-2026.10",
    "forecast": "forecast-2026.10",
    "hotspots": "hotspots-2026.10",
}


# ---------- masking ----------
def _fallback_mask(text: str) -> str:
    """TEMPORARY stand-in until Role 3's governance/privacy.py exists.
    Masks the most obvious personal details so nothing slips into the log."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[EMAIL]", text)
    text = re.sub(r"\b\d{13}\b", "[ID]", text)
    text = re.sub(r"(\+27|\b0)[\s-]?\d{2}[\s-]?\d{3}[\s-]?\d{4}\b", "[PHONE]", text)
    return text


try:
    from governance.privacy import mask_personal_info
except ImportError:  # Role 3's module isn't in the repo yet
    mask_personal_info = _fallback_mask


def summarise(text) -> str:
    """Mask personal information, tidy spaces and cut to SUMMARY_LENGTH."""
    clean = re.sub(r"\s+", " ", mask_personal_info(str(text))).strip()
    return clean if len(clean) <= SUMMARY_LENGTH else clean[: SUMMARY_LENGTH - 3] + "..."


# ---------- writing ----------
def logging_enabled() -> bool:
    return os.environ.get("REPORT_RADAR_LOGGING", "on").strip().lower() not in {"off", "0", "false", "no"}


def make_row(component: str, report_id, input_summary, output, reason) -> dict:
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "component": component,
        "report_id": "" if report_id is None else str(report_id),
        "input_summary": summarise(input_summary),
        "output": str(output),
        "reason": str(reason),
        "rules_version": RULES_VERSION.get(component, "unversioned"),
    }


def log_decisions(rows: Iterable[dict], log_file: Path | None = None) -> int:
    """Append many already-made rows at once (fast for thousands of reports).
    Returns how many rows were written."""
    if not logging_enabled():
        return 0
    path = Path(log_file or LOG_FILE)
    rows = list(rows)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not path.exists() or path.stat().st_size == 0
        with path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            if new_file:
                writer.writeheader()
            writer.writerows(rows)
    except OSError as error:  # never let logging break the real work
        print(f"Warning: could not write the decision log ({error}).")
        return 0
    return len(rows)


def log_decision(component: str, report_id, input_summary, output, reason,
                 log_file: Path | None = None) -> int:
    """Log one decision. Returns 1 if it was written, 0 if logging is off."""
    return log_decisions([make_row(component, report_id, input_summary, output, reason)], log_file)
