"""Report Radar - weekly report forecast (Week 5, Role 1: Forecast Lead).

Run from the repo root:  python forecast/forecast.py

Reads data/reports.csv, counts reports per week, tests a few simple
forecasting models on recent weeks, picks the most accurate one and
predicts the next few weeks of report volume.

Writes (all in this folder):
  output.csv               week_start, actual, forecast  (read by the dashboard)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REPORTS_FILE = ROOT / "data" / "reports.csv"
OUT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = OUT_DIR / "output.csv"

HORIZON = 4  # how many weeks ahead to forecast

REQUIRED_COLUMNS = {"timestamp", "category"}


def load_reports(path: Path = REPORTS_FILE) -> pd.DataFrame:
    """Read the reports file and parse timestamps. Rows without a valid
    timestamp are dropped because they cannot be placed in a week."""
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.dropna(subset=["timestamp"])


def weekly_counts(df: pd.DataFrame, category: str | None = None) -> pd.Series:
    """Count reports per week. Weeks start on Monday, and week_start is
    the Monday of each week. Pass a category to count only that category."""
    if category is not None:
        df = df[df["category"] == category]
    counts = (
        df.set_index("timestamp")
        .resample("W-MON", label="left", closed="left")
        .size()
    )
    counts.index.name = "week_start"
    counts.name = "reports"
    return counts


def main() -> None:
    raise NotImplementedError("Forecast pipeline not built yet.")


if __name__ == "__main__":
    main()
