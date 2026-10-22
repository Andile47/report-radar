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
from sklearn.linear_model import LinearRegression

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


def drop_partial_weeks(counts: pd.Series, timestamps: pd.Series) -> pd.Series:
    """Keep only weeks fully covered by the data.

    The first and last weeks usually contain only a few days of reports
    (e.g. data starting on a Wednesday), which would look like a sudden
    drop in volume and mislead the forecast."""
    first_day = timestamps.min().normalize()
    last_day = timestamps.max().normalize()  # last day may itself be incomplete
    week_end = counts.index + pd.Timedelta(days=7)
    full = (counts.index >= first_day) & (week_end <= last_day)
    return counts[full]


# ---------- models ----------
# Each model takes the weekly history (oldest first) and returns `horizon`
# predicted weekly counts.

MA_WINDOW = 4  # weeks averaged by the moving-average model
TREND_WINDOW = 12  # weeks used to fit the trend line


def naive(history: np.ndarray, horizon: int) -> np.ndarray:
    """Next weeks look like the most recent week."""
    return np.repeat(float(history[-1]), horizon)


def moving_average(history: np.ndarray, horizon: int, window: int = MA_WINDOW) -> np.ndarray:
    """Next weeks look like the average of the last `window` weeks."""
    return np.repeat(float(np.mean(history[-window:])), horizon)


def linear_trend(history: np.ndarray, horizon: int, window: int = TREND_WINDOW) -> np.ndarray:
    """Fit a straight line to the last `window` weeks and extend it.
    Predictions are kept at zero or above, since counts can't be negative."""
    y = np.asarray(history[-window:], dtype=float)
    x = np.arange(len(y)).reshape(-1, 1)
    model = LinearRegression().fit(x, y)
    future = np.arange(len(y), len(y) + horizon).reshape(-1, 1)
    return np.clip(model.predict(future), 0, None)


MODELS = {
    "naive": naive,
    "moving_average": moving_average,
    "linear_trend": linear_trend,
}


# ---------- evaluation ----------
BACKTEST_WEEKS = 12  # recent weeks used to test each model


def backtest(series: pd.Series, model, horizon: int = HORIZON,
             test_weeks: int = BACKTEST_WEEKS) -> float:
    """Mean absolute error (MAE) of a model on the most recent weeks.

    Rolling-origin test: pretend we are standing at each week in the test
    period, forecast the next `horizon` weeks using only the data before
    it, and compare with what actually happened. Returns the average
    miss in reports per week."""
    values = series.to_numpy(dtype=float)
    first_origin = len(values) - test_weeks
    if first_origin < TREND_WINDOW:
        raise ValueError("Not enough weeks of history to backtest.")
    errors = []
    for origin in range(first_origin, len(values) - horizon + 1):
        predicted = model(values[:origin], horizon)
        actual = values[origin:origin + horizon]
        errors.extend(np.abs(predicted - actual))
    return float(np.mean(errors))


def select_best_model(series: pd.Series) -> tuple[str, dict[str, float]]:
    """Backtest every model and return the name of the most accurate one
    (lowest MAE) together with all the scores."""
    scores = {name: backtest(series, model) for name, model in MODELS.items()}
    best = min(scores, key=scores.get)
    return best, scores


def main() -> None:
    raise NotImplementedError("Forecast pipeline not built yet.")


if __name__ == "__main__":
    main()
