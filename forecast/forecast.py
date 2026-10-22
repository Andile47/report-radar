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


def main() -> None:
    raise NotImplementedError("Forecast pipeline not built yet.")


if __name__ == "__main__":
    main()
