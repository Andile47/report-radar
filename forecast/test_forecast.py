"""Tests for the forecast module. Run from the repo root:  pytest forecast"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forecast as fc  # noqa: E402


def make_reports(start="2026-01-07", days=70, per_day=3):
    """Synthetic reports: `per_day` reports every day, alternating categories."""
    times = pd.date_range(start, periods=days * per_day, freq=f"{24 // per_day}h")
    cats = np.where(np.arange(len(times)) % 2 == 0, "water", "roads")
    return pd.DataFrame({"timestamp": times, "category": cats})


def test_weekly_counts_start_on_monday_and_sum_to_total():
    reports = make_reports()
    weekly = fc.weekly_counts(reports)
    assert (weekly.index.day_of_week == 0).all()
    assert weekly.sum() == len(reports)


def test_weekly_counts_filters_by_category():
    reports = make_reports()
    water = fc.weekly_counts(reports, "water")
    assert water.sum() == (reports["category"] == "water").sum()


def test_drop_partial_weeks_removes_incomplete_edges():
    reports = make_reports(start="2026-01-07")  # a Wednesday
    weekly = fc.drop_partial_weeks(fc.weekly_counts(reports), reports["timestamp"])
    assert weekly.index[0] == pd.Timestamp("2026-01-12")
    assert (weekly == 21).all()  # every kept week has 7 full days x 3 reports


def test_models_return_horizon_non_negative_values():
    history = np.array([30, 25, 20, 15, 10, 8, 6, 5, 4, 3, 2, 1], dtype=float)
    for model in fc.MODELS.values():
        predicted = model(history, 4)
        assert len(predicted) == 4
        assert (predicted >= 0).all()


def test_linear_trend_extends_a_straight_line():
    history = np.arange(12, dtype=float) * 2
    assert fc.linear_trend(history, 2) == pytest.approx([24.0, 26.0])


def test_moving_average_trend_follows_a_straight_line():
    history = np.arange(12, dtype=float) * 2  # 0, 2, ..., 22
    assert fc.moving_average_trend(history, 2) == pytest.approx([24.0, 26.0])


def test_backtest_is_zero_for_a_perfect_model():
    weeks = pd.date_range("2026-01-05", periods=30, freq="W-MON")
    flat = pd.Series(50.0, index=weeks)
    assert fc.backtest(flat, fc.naive) == 0


def test_backtest_needs_enough_history():
    weeks = pd.date_range("2026-01-05", periods=10, freq="W-MON")
    with pytest.raises(ValueError):
        fc.backtest(pd.Series(1.0, index=weeks), fc.naive)


def test_select_best_model_prefers_trend_on_trending_data():
    weeks = pd.date_range("2026-01-05", periods=30, freq="W-MON")
    rising = pd.Series(np.arange(30, dtype=float) * 3 + 10, index=weeks)
    best, scores = fc.select_best_model(rising)
    assert best in {"linear_trend", "moving_average_trend"}
    assert set(scores) == set(fc.MODELS)


def test_build_output_matches_dashboard_contract():
    weeks = pd.date_range("2026-01-05", periods=20, freq="W-MON")
    history = pd.Series(np.arange(20, dtype=float), index=weeks)
    future = fc.forecast_next(history, "naive")
    out = fc.build_output(history, future)

    assert list(out.columns) == ["week_start", "actual", "forecast"]
    assert len(out) == 20 + fc.HORIZON
    assert out["actual"].iloc[-fc.HORIZON:].isna().all()
    # last actual week also carries a forecast so the chart lines join
    assert out["forecast"].iloc[19] == out["actual"].iloc[19]
    pd.to_datetime(out["week_start"])  # parses, as the dashboard expects


def test_forecast_by_category_covers_every_category():
    reports = make_reports(days=200)
    weekly = fc.drop_partial_weeks(fc.weekly_counts(reports), reports["timestamp"])
    table, summary = fc.forecast_by_category(reports, weekly.index)
    assert set(table["category"]) == {"water", "roads"}
    assert set(summary) == {"water", "roads"}
    assert {"category", "week_start", "actual", "forecast", "model"} <= set(table.columns)


def test_projected_workload_has_weeks_range_and_total():
    weeks = pd.date_range("2026-11-02", periods=4, freq="W-MON")
    future = pd.Series([50.0, 52.0, 54.0, 56.0], index=weeks)
    table = fc.projected_workload(future, mae=5)
    assert len(table) == 5
    assert table["expected_reports"].iloc[-1] == 212
    assert table["week_start"].iloc[-1].startswith("Total")
    assert (table["likely_low"] <= table["expected_reports"]).all()
    assert (table["likely_high"] >= table["expected_reports"]).all()


def test_projected_workload_range_never_goes_negative():
    weeks = pd.date_range("2026-11-02", periods=4, freq="W-MON")
    table = fc.projected_workload(pd.Series(2.0, index=weeks), mae=5)
    assert (table["likely_low"] >= 0).all()


def test_plot_forecast_saves_a_chart(tmp_path):
    weeks = pd.date_range("2026-01-05", periods=20, freq="W-MON")
    history = pd.Series(np.arange(20, dtype=float) + 30, index=weeks)
    future = fc.forecast_next(history, "moving_average")
    path = tmp_path / "chart.png"
    fc.plot_forecast(history, future, 3.0, "moving_average", path)
    assert path.exists() and path.stat().st_size > 0
