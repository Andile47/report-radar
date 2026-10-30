import pandas as pd

from area_fairness import save_urgent_wait_chart, summarize_area_fairness


def test_summary_calculations_and_chart(tmp_path):
    reports = pd.DataFrame(
        [
            ["Old Alexandra", "resolved", 5, 10],
            ["Old Alexandra", "resolved", 3, 20],
            ["Tsutsumani", "resolved", 4, 20],
            ["Tsutsumani", "open", 5, None],
            ["East Bank", "resolved", 2, 5],
        ],
        columns=["ward_or_suburb", "status", "urgency", "hours_to_resolve"],
    )

    summary = summarize_area_fairness(
        reports,
        households_by_ward={"Old Alexandra": 1000, "Tsutsumani": 100},
    ).set_index("ward")

    assert summary.loc["Old Alexandra", "report_count"] == 2
    assert summary.loc["Old Alexandra", "median_hours_to_resolve"] == 15
    assert summary.loc["Old Alexandra", "median_urgent_hours_to_resolve"] == 10
    assert summary.loc["Old Alexandra", "reports_per_1000_households"] == 2
    assert summary.loc["Tsutsumani", "unresolved_share"] == 0.5
    assert summary.loc["Tsutsumani", "average_urgency"] == 4.5
    assert summary.loc["Tsutsumani", "reports_per_1000_households"] == 20
    assert bool(summary.loc["Tsutsumani", "breaks_rule"])
    assert not bool(summary.loc["Old Alexandra", "breaks_rule"])
    assert summary.index[0] == "Tsutsumani"

    chart_path = tmp_path / "area_fairness.png"
    save_urgent_wait_chart(summary.reset_index(), chart_path)
    assert chart_path.exists()