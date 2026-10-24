import pandas as pd
import pytest

from capacity import fixed_per_week, plan


def test_enough_crews_is_covered():
    r = plan(5, 14, [69, 69, 69, 69], 528)
    assert r["capacity"] == 70
    assert r["gaps"] == [1, 1, 1, 1]
    assert r["covered"] is True
    assert r["unfixed_after"] == 524
    assert r["crews_needed"] == 5


def test_too_few_crews_falls_behind():
    r = plan(4, 14, [69, 69, 69, 69], 528)
    assert r["capacity"] == 56
    assert r["gap_avg"] == -13
    assert r["covered"] is False
    assert r["unfixed_after"] == 580
    assert r["crews_needed"] == 5


def test_busy_month_needs_more():
    normal = plan(5, 14, [69] * 4, 528)
    busy = plan(5, 14, [73] * 4, 528)
    assert busy["gap_avg"] < normal["gap_avg"]
    assert busy["covered"] is False  # 70 a week is short of 73


def test_unfixed_never_below_zero():
    r = plan(10, 14, [69] * 4, 3)
    assert r["unfixed_after"] == 0


def test_zero_reports_per_crew_is_rejected():
    with pytest.raises(ValueError):
        plan(5, 0, [69] * 4, 528)


def test_fixed_per_week_counts_by_week_fixed():
    # 4 weeks, 3 fixed reports in each. The first and last weeks are dropped as part-weeks.
    starts = pd.date_range("2026-01-05", periods=4, freq="7D")
    stamps = [d + pd.Timedelta(days=k) for d in starts for k in range(3)]
    df = pd.DataFrame({"timestamp": stamps, "status": "resolved", "hours_to_resolve": 1.0})
    open_rows = pd.DataFrame({"timestamp": stamps[:2], "status": "open", "hours_to_resolve": [None, None]})
    df = pd.concat([df, open_rows], ignore_index=True)
    whole, last8 = fixed_per_week(df)
    assert whole == 3.0
    assert last8 == 3.0
