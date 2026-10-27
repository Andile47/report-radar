"""Report Radar - data check (Role 1: Data Lead).

Run from the repo root:  python data/check_data.py [path/to/reports.csv]

Checks that the dataset follows the team's agreed contract and that it is
realistic enough for the forecast and hotspot work:
  * the 10 agreed columns, in order, with no missing values where required
  * categories, urgency (1-5) and status values are valid
  * coordinates fall inside the Alexandra area
  * weekly volume has visible surges, summer has more water/road reports,
    and some wards report much more than others

Writes data/weekly_volume.png (reports per week, the surge check chart)
and exits with an error if any contract check fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = ROOT / "data" / "reports.csv"
CHART_FILE = ROOT / "data" / "weekly_volume.png"

COLUMNS = ["report_id", "timestamp", "category", "description", "ward_or_suburb",
           "latitude", "longitude", "urgency", "status", "hours_to_resolve"]
CATEGORIES = {"water", "electricity", "roads", "sanitation", "refuse", "streetlights"}
STATUSES = {"open", "in_progress", "escalated", "resolved"}
LAT_RANGE = (-26.13, -26.08)  # Alexandra, Johannesburg
LON_RANGE = (28.07, 28.13)
SUMMER, WINTER = [11, 12, 1, 2], [5, 6, 7, 8]


def contract_problems(df: pd.DataFrame) -> list[str]:
    """Return a list of broken contract rules (empty = all good)."""
    problems = []
    if list(df.columns) != COLUMNS:
        problems.append(f"columns are {list(df.columns)}, expected {COLUMNS}")
        return problems
    if df["report_id"].duplicated().any():
        problems.append(f"{df['report_id'].duplicated().sum()} duplicate report_id values")
    required = [c for c in COLUMNS if c != "hours_to_resolve"]
    empty = df[required].isna().sum()
    for col, count in empty[empty > 0].items():
        problems.append(f"{count} missing values in {col}")
    times = pd.to_datetime(df["timestamp"], errors="coerce")
    if times.isna().any():
        problems.append(f"{times.isna().sum()} timestamps do not parse")
    bad_cat = set(df["category"].dropna()) - CATEGORIES
    if bad_cat:
        problems.append(f"unknown categories: {sorted(bad_cat)}")
    if not df["urgency"].between(1, 5).all():
        problems.append("urgency outside 1-5")
    bad_status = set(df["status"].dropna()) - STATUSES
    if bad_status:
        problems.append(f"unknown status values: {sorted(bad_status)}")
    outside = ~(df["latitude"].between(*LAT_RANGE) & df["longitude"].between(*LON_RANGE))
    if outside.any():
        problems.append(f"{outside.sum()} reports with coordinates outside Alexandra")
    resolved_no_time = (df["status"] == "resolved") & df["hours_to_resolve"].isna()
    if resolved_no_time.any():
        problems.append(f"{resolved_no_time.sum()} resolved reports without hours_to_resolve")
    return problems


def realism_summary(df: pd.DataFrame) -> list[str]:
    """Plain-language checks that the patterns the team needs are present."""
    df = df.assign(timestamp=pd.to_datetime(df["timestamp"]))
    weekly = df.set_index("timestamp").resample("W-MON", label="left", closed="left").size()
    weekly = weekly.iloc[1:-1]  # first and last weeks are partial
    typical = weekly.median()
    surges = weekly[weekly >= typical * 1.3]
    lines = [f"{len(df):,} reports from {df['timestamp'].min():%d %b %Y} "
             f"to {df['timestamp'].max():%d %b %Y}",
             f"typical week {typical:.0f} reports; {len(surges)} surge week(s) at 30%+ above: "
             + ", ".join(f"{d:%d %b %Y} ({n})" for d, n in surges.items())]

    month = df["timestamp"].dt.month
    for cat in ["water", "roads"]:
        is_cat = df["category"] == cat
        summer = is_cat[month.isin(SUMMER)].mean()
        winter = is_cat[month.isin(WINTER)].mean()
        lines.append(f"{cat}: {summer:.0%} of summer reports vs {winter:.0%} of winter reports")

    wards = df["ward_or_suburb"].value_counts()
    lines.append("reports per ward: " + ", ".join(f"{w} {n}" for w, n in wards.items())
                 + f" (busiest/quietest = {wards.iloc[0] / wards.iloc[-1]:.1f}x)")
    return lines, weekly


def plot_weekly(weekly: pd.Series, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(weekly.index, weekly.to_numpy(), marker="o", markersize=3, color="#2b6cb0")
    ax.axhline(weekly.median() * 1.3, color="#e53e3e", linestyle="--", linewidth=1,
               label="Surge line (30% above a typical week)")
    ax.set_title("Synthetic reports per week (data check)")
    ax.set_ylabel("Reports per week")
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    df = pd.read_csv(path)
    problems = contract_problems(df)
    if problems:
        print("CONTRACT CHECK FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print("Contract check passed: 10 agreed columns, valid values.")
    lines, weekly = realism_summary(df)
    for line in lines:
        print("  " + line)
    if path.resolve() == DEFAULT_FILE.resolve():
        plot_weekly(weekly, CHART_FILE)
        print(f"Wrote {CHART_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
