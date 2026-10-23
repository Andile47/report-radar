"""Report Radar - synthetic citizen report generator (Role 1: Data Lead).

We have no real citizen reports, so this script makes realistic fake ones
for Alexandra, Johannesburg. Nothing here is real personal data.

Run from the repo root:

    python data/generate_reports.py --out data/reports_new.csv
    python data/generate_reports.py --force          # overwrite data/reports.csv

It will not overwrite an existing file unless you pass --force, because the
forecast, hotspot and dashboard outputs are all built from data/reports.csv.
After regenerating, re-run everything with:  python run_all.py

What makes the data realistic (so the forecast and hotspots have something
to find):
  * Seasonality - more water and road problems in the rainy summer
    (November to February), fewer in the dry winter (May to August).
  * Rain events - a few storms that spike roads, streetlights and drains.
  * Three deliberate surge periods (a January heatwave water crisis, a
    winter load-shedding wave and an early-December storm).
  * Unequal wards - Old Alexandra and East Bank report about twice as often
    as the quieter wards (needed for the fairness check in Week 6).
  * Daily rhythm - most reports arrive in the morning and early evening.

Columns (the team's agreed contract):
    report_id, timestamp, category, description, ward_or_suburb,
    latitude, longitude, urgency, status, hours_to_resolve
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "data" / "reports.csv"

COLUMNS = [
    "report_id", "timestamp", "category", "description", "ward_or_suburb",
    "latitude", "longitude", "urgency", "status", "hours_to_resolve",
]
CATEGORIES = ["water", "electricity", "roads", "sanitation", "refuse", "streetlights"]

# ---------- places ----------
# ward: (centre latitude, centre longitude, relative reporting rate)
WARDS = {
    "Old Alexandra": (-26.1030, 28.0889, 2.0),
    "East Bank": (-26.1070, 28.1000, 1.8),
    "Pan Africa": (-26.1000, 28.0959, 1.0),
    "Far East Bank": (-26.1030, 28.1141, 1.0),
    "Setswetla": (-26.0978, 28.1029, 0.7),
    "Tsutsumani": (-26.1119, 28.1092, 0.45),
}
COORD_SPREAD = 0.0023  # degrees, roughly 250 m around each ward centre
STREETS = ["Roosevelt Street", "London Road", "Selborne Street", "Vasco da Gama Street",
           "Hofmeyr Street", "Wynberg Road", "Jukskei River bank"]
# Avenues are the most common place in descriptions, then named streets.
AVENUES = [f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'} Avenue"
           for n in range(1, 23)]

# ---------- descriptions ----------
# (template, base urgency). {place} is filled with an avenue or street name.
# Includes isiZulu ("Amanzi awekho" = there is no water, "Akukho ugesi" =
# there is no electricity) because real residents write in many languages.
TEMPLATES = {
    "water": [
        ("Burst pipe flooding {place}, water running down the road", 5),
        ("No water since this morning on {place}", 3),
        ("Water outage affecting the whole block, clinic nearby has no water", 5),
        ("Communal standpipe near {place} not working", 3),
        ("Water pressure very low, only a trickle at the tap", 2),
        ("Water leaking from the meter box for days", 2),
        ("Amanzi awekho since yesterday, {place}", 3),
        ("Dirty brown water coming from taps, can't drink it", 4),
    ],
    "electricity": [
        ("Load-shedding outage lasting longer than the scheduled slot", 2),
        ("Power keeps tripping when it comes back after load-shedding", 2),
        ("Transformer exploded, whole section without power", 5),
        ("Flickering power damaging appliances", 2),
        ("Illegal connections sparking on the pole near {place}", 4),
        ("Live wires hanging low across the road at {place}", 5),
        ("Power out since last night on {place}", 3),
        ("Akukho ugesi since last night, {place}", 3),
    ],
    "roads": [
        ("Pothole filled with water after the rain, taxis swerving", 3),
        ("Small crack and sinking tar near the school gate", 1),
        ("Speed hump broken and sticking out", 2),
        ("Big pothole on {place} damaging cars", 2),
        ("Road surface washed away after heavy rain", 4),
        ("Road collapsed near the stormwater drain on {place}", 5),
        ("Open manhole cover on {place}, someone could fall in", 5),
        ("Blocked stormwater drain causing flooding at intersection", 4),
    ],
    "sanitation": [
        ("Sewage overflowing from manhole on {place}", 4),
        ("Drain blocked, grey water pooling outside our house", 2),
        ("Communal toilets overflowing, long queues and mess", 4),
        ("Bad smell from drain, sewage bubbling up", 3),
        ("Blocked sewer, raw sewage running into the yard", 5),
        ("Public toilet block locked and flooded", 3),
        ("Sewage flowing into the Jukskei near homes where children play", 5),
    ],
    "refuse": [
        ("Illegal dumping at the open lot on {place}", 2),
        ("Mound of building rubble blocking the pavement on {place}", 2),
        ("Rubbish not collected for two weeks on {place}", 2),
        ("Refuse truck missed our street again", 1),
        ("Dead animal on the roadside near {place}", 3),
        ("Overflowing bins attracting rats", 3),
        ("Burning rubbish pile with smoke near houses", 4),
    ],
    "streetlights": [
        ("Streetlight not working on {place}, very dark and unsafe", 3),
        ("Cable theft left pole without lights at {place}", 3),
        ("Whole street dark since the storm", 3),
        ("Light pole leaning and about to fall", 4),
        ("High mast light off for a week, muggings reported", 4),
        ("Streetlight on all day, wasting power", 1),
    ],
}

# ---------- seasons, rain and surges ----------
# Share of reports per category in each month (Jan..Dec), before rain/surges.
BASE_SHARE = {"water": 0.24, "electricity": 0.23, "roads": 0.18,
              "sanitation": 0.16, "refuse": 0.12, "streetlights": 0.07}
SUMMER_BOOST = {"water": 0.5, "roads": 0.6, "sanitation": 0.3}  # extra share at peak summer
WINTER_BOOST = {"electricity": 0.35, "streetlights": 0.2}       # extra share at peak winter
RAIN_BOOST = {"roads": 1.0, "sanitation": 0.8, "streetlights": 0.6, "electricity": 0.3}
DAILY_BASE = 9.8  # average reports per day across the township


def seasonal_factor(day_of_year: np.ndarray) -> np.ndarray:
    """1 at the height of summer (mid-January), -1 at mid-winter (mid-July)."""
    return np.cos(2 * np.pi * (day_of_year - 15) / 365.25)


def rain_days(days: pd.DatetimeIndex, rng: np.random.Generator) -> np.ndarray:
    """Rainy days: frequent in summer, rare in winter. Returns 0/1 per day."""
    chance = 0.05 + 0.25 * np.clip(seasonal_factor(days.day_of_year.to_numpy()), 0, None)
    return (rng.random(len(days)) < chance).astype(float)


def surge_periods(start: pd.Timestamp) -> list[dict]:
    """Three deliberate surges, placed relative to the start date so they
    always fall inside the 12 months generated."""
    def next_date(month: int, day: int) -> pd.Timestamp:
        year = start.year if (month, day) >= (start.month, start.day) else start.year + 1
        return pd.Timestamp(year=year, month=month, day=day)

    return [
        {"name": "January heatwave water crisis", "start": next_date(1, 12),
         "days": 14, "extra": 1.0, "category": "water"},
        {"name": "Winter load-shedding wave", "start": next_date(6, 15),
         "days": 10, "extra": 0.8, "category": "electricity"},
        {"name": "Early-December storm", "start": next_date(12, 8),
         "days": 7, "extra": 0.6, "category": "roads"},
    ]


def daily_plan(days: pd.DatetimeIndex, rng: np.random.Generator) -> pd.DataFrame:
    """Number of reports and category mix for each day."""
    season = seasonal_factor(days.day_of_year.to_numpy())
    rain = rain_days(days, rng)
    weekday = np.where(days.day_of_week >= 5, 0.85, 1.05)  # quieter weekends
    volume = DAILY_BASE * (1 + 0.15 * season) * (1 + 0.35 * rain) * weekday

    shares = pd.DataFrame(index=days, columns=CATEGORIES, dtype=float)
    for cat in CATEGORIES:
        share = np.full(len(days), BASE_SHARE[cat])
        share *= 1 + SUMMER_BOOST.get(cat, 0) * np.clip(season, 0, None)
        share *= 1 + WINTER_BOOST.get(cat, 0) * np.clip(-season, 0, None)
        share *= 1 + RAIN_BOOST.get(cat, 0) * rain
        shares[cat] = share

    for surge in surge_periods(days[0]):
        in_surge = (days >= surge["start"]) & (
            days < surge["start"] + pd.Timedelta(days=surge["days"]))
        volume[in_surge] *= 1 + surge["extra"]
        shares.loc[in_surge, surge["category"]] *= 2.5

    shares = shares.div(shares.sum(axis=1), axis=0)
    shares["n"] = rng.poisson(volume)
    return shares


def fill_place(template: str, rng: np.random.Generator) -> str:
    if "{place}" not in template:
        return template
    pool = AVENUES if rng.random() < 0.8 else STREETS
    place = rng.choice(pool)
    return template.replace("{place}", str(place))


def report_time(day: pd.Timestamp, rng: np.random.Generator) -> pd.Timestamp:
    """Morning and early-evening peaks, quiet nights."""
    hour_weights = np.array([2, 1.5, 1, 1, 3, 5, 9, 10, 9, 7, 6, 5,
                             5, 5, 5, 6, 8, 9, 10, 8, 6, 5, 3, 2], dtype=float)
    hour = rng.choice(24, p=hour_weights / hour_weights.sum())
    return day + pd.Timedelta(hours=int(hour), seconds=int(rng.integers(0, 3600)))


def outcome(urgency: int, timestamp: pd.Timestamp, end: pd.Timestamp,
            rng: np.random.Generator) -> tuple[str, float]:
    """Status and resolution time. Urgent reports are fixed faster; recent
    reports are more likely to still be open."""
    median_hours = {1: 170, 2: 40, 3: 38, 4: 43, 5: 22}[urgency]
    hours = float(np.round(rng.lognormal(np.log(median_hours), 0.6), 1))
    age_hours = (end - timestamp).total_seconds() / 3600
    if hours > age_hours or rng.random() < 0.06:
        status = rng.choice(["open", "in_progress", "escalated"], p=[0.5, 0.2, 0.3])
        return str(status), np.nan
    return "resolved", hours


def generate(n_months: int = 12, end: str | None = None, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end_ts = pd.Timestamp(end) if end else pd.Timestamp.today().normalize()
    days = pd.date_range(end=end_ts - pd.Timedelta(days=1), periods=int(n_months * 30.4), freq="D")
    plan = daily_plan(days, rng)

    ward_names = list(WARDS)
    ward_weights = np.array([WARDS[w][2] for w in ward_names])
    ward_weights /= ward_weights.sum()

    rows = []
    for day, row in plan.iterrows():
        cats = rng.choice(CATEGORIES, size=int(row["n"]), p=row[CATEGORIES].to_numpy(dtype=float))
        for cat in cats:
            template, base_urgency = TEMPLATES[cat][rng.integers(len(TEMPLATES[cat]))]
            urgency = int(np.clip(base_urgency + rng.choice([-1, 0, 0, 0, 0, 0, 0, 1]), 1, 5))
            ward = rng.choice(ward_names, p=ward_weights)
            lat, lon, _ = WARDS[ward]
            timestamp = report_time(day, rng)
            status, hours = outcome(urgency, timestamp, end_ts, rng)
            rows.append({
                "timestamp": timestamp,
                "category": cat,
                "description": fill_place(template, rng),
                "ward_or_suburb": ward,
                "latitude": round(float(rng.normal(lat, COORD_SPREAD)), 6),
                "longitude": round(float(rng.normal(lon, COORD_SPREAD)), 6),
                "urgency": urgency,
                "status": status,
                "hours_to_resolve": hours,
            })

    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    df.insert(0, "report_id", [f"ALX-{i:06d}" for i in range(1, len(df) + 1)])
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df[COLUMNS]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--end", help="last day of data (YYYY-MM-DD), default today")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true", help="overwrite an existing file")
    args = parser.parse_args()

    if args.out.exists() and not args.force:
        raise SystemExit(f"{args.out} already exists. Pass --force to overwrite it, "
                         f"or --out to write somewhere else.")
    df = generate(args.months, args.end, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df):,} reports to {args.out}")
    for surge in surge_periods(pd.Timestamp(df["timestamp"].iloc[0]).normalize()):
        print(f"  surge: {surge['name']} from {surge['start']:%d %b %Y} ({surge['days']} days)")


if __name__ == "__main__":
    main()
