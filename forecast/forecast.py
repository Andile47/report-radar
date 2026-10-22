"""Report Radar - weekly report forecast (Week 5, Role 1: Forecast Lead).

Run from the repo root:  python forecast/forecast.py

Reads data/reports.csv, counts reports per week, tests a few simple
forecasting models on recent weeks, picks the most accurate one and
predicts the next few weeks of report volume.

Writes (all in this folder):
  output.csv               week_start, actual, forecast  (read by the dashboard)
  output_by_category.csv   category, week_start, actual, forecast, model
  metrics.json             backtest accuracy of each model
  projected_workload.csv   next 4 weeks: expected reports, likely range, total
  insights.md              3 sentences on the forecast + the workload table
  forecast_chart.png       past volume, moving average, trend line, forecast
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

ROOT = Path(__file__).resolve().parent.parent
REPORTS_FILE = ROOT / "data" / "reports.csv"
OUT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = OUT_DIR / "output.csv"
CATEGORY_FILE = OUT_DIR / "output_by_category.csv"
METRICS_FILE = OUT_DIR / "metrics.json"
INSIGHTS_FILE = OUT_DIR / "insights.md"
WORKLOAD_FILE = OUT_DIR / "projected_workload.csv"
CHART_FILE = OUT_DIR / "forecast_chart.png"

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


def trend_slope(history: np.ndarray, window: int = TREND_WINDOW) -> float:
    """Change in reports per week, from a straight line fitted to the last
    `window` weeks (positive = rising, negative = falling)."""
    y = np.asarray(history[-window:], dtype=float)
    x = np.arange(len(y)).reshape(-1, 1)
    return float(LinearRegression().fit(x, y).coef_[0])


def moving_average_trend(history: np.ndarray, horizon: int,
                         window: int = MA_WINDOW) -> np.ndarray:
    """Moving average plus a trend line: start from the average of the
    last `window` weeks, then add the trend's weekly change for each week
    ahead. The average sits in the middle of its window, (window - 1) / 2
    weeks before the latest week, so the steps are counted from there."""
    level = float(np.mean(history[-window:]))
    slope = trend_slope(history)
    steps = np.arange(1, horizon + 1) + (window - 1) / 2
    return np.clip(level + slope * steps, 0, None)


MODELS = {
    "naive": naive,
    "moving_average": moving_average,
    "linear_trend": linear_trend,
    "moving_average_trend": moving_average_trend,
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


def forecast_next(series: pd.Series, model_name: str, horizon: int = HORIZON) -> pd.Series:
    """Forecast the `horizon` weeks after the last week in `series`,
    using all of the history."""
    predicted = MODELS[model_name](series.to_numpy(dtype=float), horizon)
    weeks = pd.date_range(
        series.index[-1] + pd.Timedelta(weeks=1), periods=horizon, freq="W-MON"
    )
    return pd.Series(predicted.round(1), index=weeks, name="forecast")


def build_output(history: pd.Series, future: pd.Series) -> pd.DataFrame:
    """Combine history and forecast in the dashboard's format:
    week_start, actual, forecast.

    History rows have `actual` filled; future rows have `forecast` filled.
    The last history week carries both values so the two lines join up
    on the dashboard chart instead of leaving a gap."""
    past = pd.DataFrame(
        {"week_start": history.index, "actual": history.to_numpy(dtype=float),
         "forecast": np.nan}
    )
    past.loc[past.index[-1], "forecast"] = past["actual"].iloc[-1]
    ahead = pd.DataFrame(
        {"week_start": future.index, "actual": np.nan,
         "forecast": future.to_numpy()}
    )
    out = pd.concat([past, ahead], ignore_index=True)
    out["week_start"] = out["week_start"].dt.strftime("%Y-%m-%d")
    return out


def forecast_by_category(reports: pd.DataFrame, weeks: pd.Index) -> tuple[pd.DataFrame, dict]:
    """Run the same model selection and forecast for each category, so a
    surge in one service (e.g. water) is visible even if the total is flat.

    Returns a long table (category, week_start, actual, forecast, model)
    and a summary of the chosen model and MAE per category."""
    frames, summary = [], {}
    for category in sorted(reports["category"].dropna().unique()):
        weekly = weekly_counts(reports, category).reindex(weeks, fill_value=0)
        best, scores = select_best_model(weekly)
        out = build_output(weekly, forecast_next(weekly, best))
        out.insert(0, "category", category)
        out["model"] = best
        frames.append(out)
        summary[category] = {"model": best, "mae": round(scores[best], 2)}
    return pd.concat(frames, ignore_index=True), summary


def build_metrics(weekly: pd.Series, best: str, scores: dict[str, float],
                  category_summary: dict) -> dict:
    """Accuracy summary saved alongside the forecast so the team can quote
    how reliable it is. MAE is also shown as a % of an average week."""
    mean_week = float(weekly.mean())
    return {
        "history_start": f"{weekly.index[0]:%Y-%m-%d}",
        "history_end": f"{weekly.index[-1]:%Y-%m-%d}",
        "weeks_of_history": int(len(weekly)),
        "horizon_weeks": HORIZON,
        "backtest_weeks": BACKTEST_WEEKS,
        "average_reports_per_week": round(mean_week, 1),
        "selected_model": best,
        "mae_by_model": {name: round(mae, 2) for name, mae in scores.items()},
        "selected_mae_pct_of_average_week": round(100 * scores[best] / mean_week, 1),
        "by_category": category_summary,
    }


SURGE_THRESHOLD = 0.15  # forecast this far above the recent average = surge


def change_vs_recent(history: pd.Series, future: pd.Series) -> float:
    """Fractional change of the forecast average vs the last HORIZON weeks."""
    recent = float(history.iloc[-HORIZON:].mean())
    return (float(future.mean()) - recent) / recent if recent else 0.0


def projected_workload(future: pd.Series, mae: float) -> pd.DataFrame:
    """Table of expected reports for each of the next weeks, with a likely
    range (forecast +/- the backtest MAE) and a total for the whole period
    (about a month)."""
    low = (future - mae).clip(lower=0)
    high = future + mae
    table = pd.DataFrame({
        "week_start": future.index.strftime("%Y-%m-%d"),
        "expected_reports": future.round().astype(int).to_numpy(),
        "likely_low": low.round().astype(int).to_numpy(),
        "likely_high": high.round().astype(int).to_numpy(),
    })
    total = pd.DataFrame([{
        "week_start": f"Total next {len(future)} weeks",
        "expected_reports": int(table["expected_reports"].sum()),
        "likely_low": int(table["likely_low"].sum()),
        "likely_high": int(table["likely_high"].sum()),
    }])
    return pd.concat([table, total], ignore_index=True)


def category_changes(by_category: pd.DataFrame) -> pd.DataFrame:
    """For each category: recent weekly average, forecast weekly average,
    and the change between them, biggest rise first."""
    rows = []
    for category, part in by_category.groupby("category"):
        hist = part.dropna(subset=["actual"])["actual"]
        ahead = part[part["actual"].isna()]["forecast"]
        recent = float(hist.iloc[-HORIZON:].mean())
        expected = float(ahead.mean())
        rows.append({
            "category": category,
            "recent_per_week": recent,
            "forecast_per_week": expected,
            "change_per_week": expected - recent,
            "change_pct": (expected - recent) / recent if recent else 0.0,
        })
    return pd.DataFrame(rows).sort_values("change_per_week", ascending=False)


def write_insights(weekly: pd.Series, future: pd.Series, metrics: dict,
                   by_category: pd.DataFrame, workload: pd.DataFrame) -> str:
    """Turn the forecast into 3 plain sentences for the dashboard: next week
    and next month, what is driving any change (with a surge alert if the
    total or a category is SURGE_THRESHOLD above recent weeks), and how
    accurate the forecast usually is. The workload table is added below."""
    change = change_vs_recent(weekly, future)
    direction = ("up" if change > 0.02 else "down" if change < -0.02
                 else "about level")
    month_total = workload["expected_reports"].iloc[-1]
    period_end = future.index[-1] + pd.Timedelta(days=6)
    lines = [
        f"Expect about {future.iloc[0]:.0f} reports next week and about "
        f"{month_total} over the next {HORIZON} weeks "
        f"({future.index[0]:%d %b} to {period_end:%d %b %Y}), "
        f"{direction} ({change:+.0%}) on the last {HORIZON} weeks."
    ]

    changes = category_changes(by_category)
    surges = changes[changes["change_pct"] >= SURGE_THRESHOLD]
    riser, faller = changes.iloc[0], changes.iloc[-1]
    if change >= SURGE_THRESHOLD or len(surges):
        names = ", ".join(f"{r.category} ({r.change_pct:+.0%})"
                          for r in surges.itertuples()) or "all teams"
        driver = f"driven mainly by {riser.category}" if len(surges) else ""
        lines.append(f"**Surge alert:** volume is forecast to rise sharply "
                     f"{driver} - plan extra capacity for {names}.".replace("  ", " "))
    elif riser.change_pct > 0.02:
        lines.append(
            f"No surge is expected; the main rise is in {riser.category} "
            f"(about {riser.change_per_week:+.1f} reports a week, "
            f"{riser.change_pct:+.0%}), so keep an eye on that team"
            + (f", while {faller.category} is easing ({faller.change_pct:+.0%})."
               if faller.change_pct < -0.02 else ".")
        )
    else:
        lines.append(f"No surge is expected: no category is forecast to rise more "
                     f"than {SURGE_THRESHOLD:.0%}, so current staffing should cope.")

    average = metrics["average_reports_per_week"]
    peak_week = weekly.idxmax()
    lines.append(
        f"For context, the average over the full history is {average:.0f} a week and the "
        f"busiest week was {peak_week:%d %b %Y} ({weekly.max():.0f} reports); "
        f"the forecast is typically off by about "
        f"{metrics['mae_by_model'][metrics['selected_model']]:.0f} reports a week "
        f"({metrics['selected_mae_pct_of_average_week']:.0f}% of an average week)."
    )
    text = " ".join(lines)

    table_md = ["| Week starting | Expected reports | Likely range |",
                "| --- | --- | --- |"]
    for row in workload.itertuples():
        label = f"**{row.week_start}**" if row.week_start.startswith("Total") else row.week_start
        table_md.append(f"| {label} | {row.expected_reports} | "
                        f"{row.likely_low}-{row.likely_high} |")
    INSIGHTS_FILE.write_text(
        "# Forecast insights\n\n" + text + "\n\n## Projected workload\n\n"
        + "\n".join(table_md) + "\n\nLikely range = forecast plus or minus the "
        "average backtest error.\n"
    )
    return text


def plot_forecast(weekly: pd.Series, future: pd.Series, mae: float,
                  best: str, path: Path) -> None:
    """Save a chart of past weekly volume, the 4-week moving average, the
    trend line, and the forecast with its likely range."""
    import matplotlib
    matplotlib.use("Agg")  # write to a file, no window needed
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(weekly.index, weekly.to_numpy(), color="#4a5568", marker="o",
            markersize=3, linewidth=1.2, label="Reports per week (actual)")
    ax.plot(weekly.index, weekly.rolling(MA_WINDOW).mean(), color="#3182ce",
            linewidth=2, label=f"{MA_WINDOW}-week moving average")

    # trend line: fitted to the last TREND_WINDOW weeks, extended forward
    values = weekly.to_numpy(dtype=float)
    fit_weeks = weekly.index[-TREND_WINDOW:]
    y = values[-TREND_WINDOW:]
    x = np.arange(len(y)).reshape(-1, 1)
    line = LinearRegression().fit(x, y)
    trend_x = np.arange(len(y) + len(future)).reshape(-1, 1)
    trend_weeks = fit_weeks.append(future.index)
    ax.plot(trend_weeks, np.clip(line.predict(trend_x), 0, None), color="#dd6b20",
            linestyle="--", linewidth=1.5,
            label=f"Trend line (last {TREND_WINDOW} weeks)")

    joined = pd.concat([weekly.iloc[-1:], future])
    ax.plot(joined.index, joined.to_numpy(), color="#e53e3e", marker="o",
            linewidth=2.2, label=f"Forecast ({best.replace('_', ' ')})")
    ax.fill_between(future.index, (future - mae).clip(lower=0), future + mae,
                    color="#e53e3e", alpha=0.15, label="Likely range")
    ax.axvline(weekly.index[-1], color="#a0aec0", linestyle=":", linewidth=1)

    ax.set_title("Report Radar: weekly report volume and 4-week forecast")
    ax.set_xlabel("Week starting")
    ax.set_ylabel("Reports per week")
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    reports = load_reports()
    weekly = drop_partial_weeks(weekly_counts(reports), reports["timestamp"])
    best, scores = select_best_model(weekly)
    future = forecast_next(weekly, best)

    build_output(weekly, future).to_csv(OUTPUT_FILE, index=False)
    by_category, category_summary = forecast_by_category(reports, weekly.index)
    by_category.to_csv(CATEGORY_FILE, index=False)
    metrics = build_metrics(weekly, best, scores, category_summary)
    METRICS_FILE.write_text(json.dumps(metrics, indent=2) + "\n")
    workload = projected_workload(future, scores[best])
    workload.to_csv(WORKLOAD_FILE, index=False)
    insights = write_insights(weekly, future, metrics, by_category, workload)
    plot_forecast(weekly, future, scores[best], best, CHART_FILE)

    print(f"Weeks of history: {len(weekly)} "
          f"({weekly.index[0]:%Y-%m-%d} to {weekly.index[-1]:%Y-%m-%d})")
    for name, mae in sorted(scores.items(), key=lambda kv: kv[1]):
        print(f"  {name:<21} MAE {mae:5.1f} reports/week")
    print(f"Selected model: {best}")
    for category, info in category_summary.items():
        print(f"  {category:<13} {info['model']:<21} MAE {info['mae']:5.1f}")
    print("\nProjected workload:\n" + workload.to_string(index=False) + "\n")
    for path in (OUTPUT_FILE, CATEGORY_FILE, METRICS_FILE, WORKLOAD_FILE,
                 INSIGHTS_FILE, CHART_FILE):
        print(f"Wrote {path.relative_to(ROOT)}")
    print("\n" + insights)


if __name__ == "__main__":
    main()
