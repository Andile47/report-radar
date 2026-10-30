"""Summarize service outcomes by ward and flag urgent waiting-time gaps."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "reports.csv"
OUTPUT_DIR = Path(__file__).resolve().parent
SUMMARY_FILE = OUTPUT_DIR / "area_fairness.csv"
CHART_FILE = OUTPUT_DIR / "area_fairness.png"

WARDS = [
    "Old Alexandra",
    "East Bank",
    "Pan Africa",
    "Far East Bank",
    "Setswetla",
    "Tsutsumani",
]

# ASSUMPTION ONLY: illustrative household counts, not census or municipal data.
# Replace with the municipality's latest official household counts for matching
# ward boundaries, and record the source and reference date before using rates.
ASSUMED_HOUSEHOLDS_BY_WARD = {
    "Old Alexandra": 8000,
    "East Bank": 5500,
    "Pan Africa": 4000,
    "Far East Bank": 4500,
    "Setswetla": 2500,
    "Tsutsumani": 2000,
}

FAIRNESS_MULTIPLIER = 1.5


def summarize_area_fairness(
    reports: pd.DataFrame,
    households_by_ward: dict[str, int] | None = None,
) -> pd.DataFrame:
    """Return one row per known or observed ward, including fairness flags."""
    required_columns = {"ward_or_suburb", "status", "urgency", "hours_to_resolve"}
    missing_columns = required_columns.difference(reports.columns)
    if missing_columns:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing_columns)))

    households = (
        households_by_ward
        if households_by_ward is not None
        else ASSUMED_HOUSEHOLDS_BY_WARD
    )
    data = reports.copy()
    data["ward_or_suburb"] = data["ward_or_suburb"].fillna("Unknown").astype(str).str.strip()
    data["status"] = data["status"].fillna("").astype(str).str.strip().str.lower()
    data["urgency"] = pd.to_numeric(data["urgency"], errors="coerce")
    data["hours_to_resolve"] = pd.to_numeric(data["hours_to_resolve"], errors="coerce")

    observed_wards = sorted(set(data["ward_or_suburb"]) - set(WARDS))
    wards = WARDS + observed_wards
    rows = []

    for ward in wards:
        ward_reports = data.loc[data["ward_or_suburb"] == ward]
        resolved = ward_reports.loc[
            ward_reports["status"].eq("resolved") & ward_reports["hours_to_resolve"].notna()
        ]
        resolved_urgent = resolved.loc[resolved["urgency"].ge(4)]
        household_count = households.get(ward)

        rows.append(
            {
                "ward": ward,
                "report_count": len(ward_reports),
                "median_hours_to_resolve": resolved["hours_to_resolve"].median(),
                "median_urgent_hours_to_resolve": resolved_urgent[
                    "hours_to_resolve"
                ].median(),
                "unresolved_share": (
                    ward_reports["status"].ne("resolved").mean()
                    if not ward_reports.empty
                    else float("nan")
                ),
                "average_urgency": ward_reports["urgency"].mean(),
                "assumed_households": household_count,
                "reports_per_1000_households": (
                    len(ward_reports) / household_count * 1000
                    if household_count is not None and household_count > 0
                    else float("nan")
                ),
            }
        )

    summary = pd.DataFrame(rows)
    available_urgent_medians = summary["median_urgent_hours_to_resolve"].dropna()
    threshold = (
        available_urgent_medians.min() * FAIRNESS_MULTIPLIER
        if not available_urgent_medians.empty
        else float("nan")
    )
    summary["breaks_rule"] = summary["median_urgent_hours_to_resolve"].gt(threshold)
    return summary.sort_values(
        "median_urgent_hours_to_resolve", ascending=False, na_position="last"
    ).reset_index(drop=True)


def save_urgent_wait_chart(summary: pd.DataFrame, output_path: Path = CHART_FILE) -> None:
    """Save ward urgent-resolution medians with the fairness threshold."""
    available = summary.dropna(subset=["median_urgent_hours_to_resolve"])
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(
        available["ward"],
        available["median_urgent_hours_to_resolve"],
        color="#287c78",
    )
    ax.set_ylabel("Median hours to resolve (hours)")
    ax.set_title("Urgent reports (urgency 4-5): median resolution time by ward")
    ax.tick_params(axis="x", labelrotation=25)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    if not available.empty:
        threshold = available["median_urgent_hours_to_resolve"].min() * FAIRNESS_MULTIPLIER
        ax.axhline(
            threshold,
            color="#b5473c",
            linestyle="--",
            linewidth=1.8,
            label=f"Fairness threshold ({FAIRNESS_MULTIPLIER:.1f}x fastest): {threshold:.1f} h",
        )
        ax.legend()
    else:
        ax.text(0.5, 0.5, "No resolved urgent reports available", ha="center", va="center")

    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> None:
    reports = pd.read_csv(DATA_FILE)
    summary = summarize_area_fairness(reports)
    summary.to_csv(SUMMARY_FILE, index=False, float_format="%.2f")
    save_urgent_wait_chart(summary)

    threshold = summary["median_urgent_hours_to_resolve"].min() * FAIRNESS_MULTIPLIER
    flagged_wards = summary.loc[summary["breaks_rule"], "ward"].tolist()
    print(f"Saved ward fairness summary: {SUMMARY_FILE}")
    print(f"Saved urgent waiting-time chart: {CHART_FILE}")
    print(f"Fairness threshold: {threshold:.2f} hours")
    print("Wards breaking the rule: " + (", ".join(flagged_wards) or "none"))


if __name__ == "__main__":
    main()