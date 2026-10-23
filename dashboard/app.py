"""Report Radar - Week 5 dashboard (Role 5: Dashboard, Integration and Docs Lead).

Run from the repo root:  streamlit run dashboard/app.py
(Build every file first with:  python run_all.py)

Written for readers without a technical background: the page opens with a
plain-language summary, every number says what it means, and technical
detail is tucked into "more detail" sections.

Shows the team's work in three tabs:
  Workload forecast   forecast/output.csv, projected_workload.csv,
                      output_by_category.csv, insights.md          (Forecast Lead)
  Problem areas       hotspots/clusters.csv, hotspot_map.html,
                      insights.md                                  (Hotspot Lead)
  Reports             intake/data/reports_classified.csv           (Intake Lead)
                      falls back to data/reports.csv               (Data Lead)

If a file is missing, that part shows clearly labelled placeholder data so
the dashboard always runs while teammates finish their parts.
"""
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
REPORTS_FILE = ROOT / "data" / "reports.csv"
CLASSIFIED_FILE = ROOT / "intake" / "data" / "reports_classified.csv"
FORECAST_FILE = ROOT / "forecast" / "output.csv"
FORECAST_CATEGORY_FILE = ROOT / "forecast" / "output_by_category.csv"
WORKLOAD_FILE = ROOT / "forecast" / "projected_workload.csv"
FORECAST_INSIGHTS = ROOT / "forecast" / "insights.md"
FORECAST_METRICS = ROOT / "forecast" / "metrics.json"
CLUSTERS_FILE = ROOT / "hotspots" / "clusters.csv"
MAP_FILE = ROOT / "hotspots" / "hotspot_map.html"
HOTSPOT_INSIGHTS = ROOT / "hotspots" / "insights.md"

CATEGORIES = ["water", "electricity", "roads", "sanitation", "refuse", "streetlights"]

# Plain-language names for what the data stores as codes.
PROBLEM_NAMES = {
    "water": "Water",
    "electricity": "Electricity",
    "roads": "Roads",
    "sanitation": "Sewage & toilets",
    "refuse": "Rubbish",
    "streetlights": "Streetlights",
    "other": "Unclear - needs checking",
}
URGENCY_NAMES = {1: "1 - Cosmetic", 2: "2 - Low", 3: "3 - Medium", 4: "4 - High",
                 5: "5 - Danger to life"}
STATUS_NAMES = {"open": "Not started", "in_progress": "Being fixed",
                "escalated": "Escalated", "resolved": "Fixed"}
URGENCY_SCALE = ("Urgency scale: 1 = cosmetic, 2 = low, 3 = medium (a service is down), "
                 "4 = high (health or safety risk), 5 = danger to life.")

COLOR_ACTUAL = "#2c5282"    # dark blue: what really happened
COLOR_FORECAST = "#dd6b20"  # orange: what we expect

st.set_page_config(page_title="Report Radar", layout="wide")


# ---------- placeholder data (used only if a real file is missing) ----------
def placeholder_reports() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 300
    return pd.DataFrame(
        {
            "report_id": [f"PH-{i:04d}" for i in range(1, n + 1)],
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="14h"),
            "category": rng.choice(CATEGORIES, n),
            "description": ["Placeholder report"] * n,
            "ward_or_suburb": rng.choice(["Ward A", "Ward B", "Ward C"], n),
            "latitude": -26.10 + rng.normal(0, 0.005, n),
            "longitude": 28.10 + rng.normal(0, 0.005, n),
            "urgency": rng.integers(1, 6, n),
            "status": rng.choice(["open", "in_progress", "resolved"], n),
            "hours_to_resolve": rng.integers(2, 120, n),
        }
    )


def placeholder_forecast() -> pd.DataFrame:
    weeks = pd.date_range("2026-07-06", periods=16, freq="W-MON")
    actual = [40, 44, 41, 52, 49, 55, 60, 58, 63, 70, 66, 72] + [None] * 4
    forecast = [None] * 11 + [72, 74, 77, 80, 83]
    return pd.DataFrame({"week_start": weeks, "actual": actual, "forecast": forecast})


def placeholder_clusters() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "rank": [1, 2, 3, 4, 5],
            "area_name": ["Area 1", "Area 2", "Area 3", "Area 4", "Area 5"],
            "report_count": [120, 95, 70, 50, 30],
            "latitude": [-26.100, -26.105, -26.098, -26.103, -26.111],
            "longitude": [28.089, 28.100, 28.103, 28.114, 28.109],
        }
    )


# ---------- loading ----------
@st.cache_data
def load_csv(path: Path, date_cols=()):
    return pd.read_csv(path, parse_dates=list(date_cols)) if path.exists() else None


def read_text(path: Path) -> str | None:
    return path.read_text() if path.exists() else None


def load_reports() -> tuple[pd.DataFrame, str]:
    """Classified reports if the intake step has run, else the raw dataset,
    else placeholders. Returns the data and where it came from."""
    classified = load_csv(CLASSIFIED_FILE, ["timestamp"])
    if classified is not None:
        df = classified.rename(columns={"category": "dataset_category",
                                        "urgency": "dataset_urgency"})
        df["category"] = df["predicted_category"]
        df["urgency"] = df["predicted_urgency"]
        return df, "classifier"
    raw = load_csv(REPORTS_FILE, ["timestamp"])
    if raw is not None:
        raw["review_required"] = False
        return raw, "dataset"
    df = placeholder_reports()
    df["review_required"] = False
    return df, "placeholder"


def problem(code) -> str:
    return PROBLEM_NAMES.get(str(code), str(code).capitalize())


def day_month(date) -> str:
    return f"{pd.Timestamp(date).day} {pd.Timestamp(date):%b}"


def category_trends(by_cat: pd.DataFrame | None) -> pd.DataFrame:
    """Per problem type: recent weekly average vs forecast weekly average."""
    if by_cat is None:
        return pd.DataFrame(columns=["category", "recent", "expected", "change"])
    rows = []
    for cat, part in by_cat.groupby("category"):
        recent = part["actual"].dropna().tail(4).mean()
        expected = part.loc[part["actual"].isna(), "forecast"].mean()
        rows.append({"category": cat, "recent": recent, "expected": expected,
                     "change": (expected - recent) / recent if recent else 0.0})
    return pd.DataFrame(rows).sort_values("change", ascending=False)


reports, reports_source = load_reports()
forecast = load_csv(FORECAST_FILE, ["week_start"])
fc_ph = forecast is None
forecast = placeholder_forecast() if fc_ph else forecast
clusters = load_csv(CLUSTERS_FILE)
cl_ph = clusters is None
clusters = placeholder_clusters() if cl_ph else clusters
workload = load_csv(WORKLOAD_FILE)
by_cat = load_csv(FORECAST_CATEGORY_FILE, ["week_start"])
trends = category_trends(by_cat)

history = forecast.dropna(subset=["actual"])
future = forecast[forecast["actual"].isna()]
last_week = history["week_start"].max()
if workload is not None and len(workload) > 1:
    weeks_ahead = workload.iloc[:-1]
    next_week = int(weeks_ahead["expected_reports"].iloc[0])
    next_low, next_high = int(weeks_ahead["likely_low"].iloc[0]), int(weeks_ahead["likely_high"].iloc[0])
    month_total = int(workload["expected_reports"].iloc[-1])
    month_low, month_high = int(workload["likely_low"].iloc[-1]), int(workload["likely_high"].iloc[-1])
else:
    weeks_ahead = None
    next_week = int(round(future["forecast"].iloc[0])) if len(future) else 0
    next_low = next_high = next_week
    month_total = int(round(future["forecast"].sum()))
    month_low = month_high = month_total
recent_avg = history["actual"].tail(4).mean()
change = (future["forecast"].mean() - recent_avg) / recent_avg if len(future) and recent_avg else 0.0
surge = change >= 0.15 or (len(trends) and trends["change"].max() >= 0.15)

ranked = clusters.sort_values("report_count", ascending=False).reset_index(drop=True)
total_clustered = ranked["report_count"].sum()
top_two_share = ranked["report_count"].head(2).sum() / total_clustered if total_clustered else 0


def change_words(value: float) -> str:
    if value >= 0.15:
        return f"a big rise ({value:.0%} more)"
    if value > 0.03:
        return f"a small rise ({value:.0%} more)"
    if value < -0.03:
        return f"a fall ({abs(value):.0%} fewer)"
    return "about the same as recent weeks"


# ---------- header and summary ----------
st.title("Report Radar")
st.caption("Citizen reports in Alexandra, Johannesburg: what is coming next month, and where. "
           "All data is synthetic (realistic but not real).")

missing = [name for name, ph in [("reports", reports_source == "placeholder"),
                                 ("forecast", fc_ph), ("problem areas", cl_ph)] if ph]
if missing:
    st.warning("Some parts show EXAMPLE data because the real files aren't built yet: "
               + ", ".join(missing) + ". Run `python run_all.py` to build them.")

watch = trends.iloc[0] if len(trends) else None
summary = [
    f"**Next week:** about **{next_week} reports** expected, {change_words(change)}.",
    f"**Next 4 weeks:** about **{month_total} reports** in total "
    f"(most likely between {month_low} and {month_high}).",
]
if watch is not None and watch["change"] > 0.03:
    summary.append(f"**Keep an eye on:** {problem(watch['category']).lower()} problems, the only type "
                   f"that is rising (from about {watch['recent']:.0f} to {watch['expected']:.0f} a week).")
if len(ranked) >= 2:
    summary.append(f"**Busiest areas:** {ranked['area_name'].iloc[0]} and {ranked['area_name'].iloc[1]} "
                   f"produce {top_two_share:.0%} of all reports, so extra crews help most there.")
box = st.error if surge else st.success
box(("**Surge alert: plan extra capacity.**\n\n" if surge else
     "**No surge expected this month.** Current staffing should cope.\n\n")
    + "\n".join(f"- {line}" for line in summary))

# ---------- sidebar filters ----------
st.sidebar.header("Filter the reports")
st.sidebar.caption("These change the numbers below the summary and the Reports tab. "
                   "The forecast and problem areas always use every report.")
codes = sorted(reports["category"].dropna().unique(), key=lambda c: problem(c))
chosen = st.sidebar.multiselect("Type of problem", codes, default=codes, format_func=problem)
wards = sorted(reports["ward_or_suburb"].dropna().unique())
chosen_wards = st.sidebar.multiselect("Area", wards, default=wards)
min_urg = st.sidebar.select_slider("Only show urgency of at least", options=[1, 2, 3, 4, 5],
                                   value=1, format_func=lambda u: URGENCY_NAMES[u])
search = st.sidebar.text_input("Search what residents wrote", placeholder="e.g. pothole")

view = reports[reports["category"].isin(chosen)
               & reports["ward_or_suburb"].isin(chosen_wards)
               & (reports["urgency"] >= min_urg)]
if search:
    view = view[view["description"].str.contains(search, case=False, na=False)]

not_fixed = view["status"] != "resolved" if "status" in view else pd.Series(False, index=view.index)
urgent = view["urgency"] >= 4
needs_check = int(view["review_required"].sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Reports in the last year", f"{len(view):,}")
c2.metric("Urgent (high or danger to life)", f"{urgent.sum():,}",
          help="Urgency 4 or 5: a health or safety risk, or danger to life.")
c3.metric("Not fixed yet", f"{not_fixed.sum():,}",
          help="Reports that are not started, being fixed or escalated.")
c4.metric("Urgent and not fixed yet", f"{(urgent & not_fixed).sum():,}",
          help="These need attention first. See them in the Reports tab.")
st.caption(URGENCY_SCALE + (f" {needs_check:,} reports were too unclear to sort automatically "
                            "and need a person to check them." if needs_check else
                            " Every report was sorted automatically; none need checking by hand."))

# ---------- tabs ----------
tab_f, tab_h, tab_r = st.tabs(["Workload forecast", "Problem areas", "Reports"])

with tab_f:
    st.subheader("How many reports to expect")
    with st.expander("How to read this page"):
        st.markdown(
            "- The **dark blue line** is how many reports arrived each week over the past year.\n"
            "- The **orange line** is what we expect over the next 4 weeks, and the **shaded "
            "band** is the likely range: real numbers will usually land inside it.\n"
            "- The **dotted line** marks the last full week of data.\n"
            "- Peaks are surges: the biggest was in January, when water problems spiked."
        )
    m1, m2, m3 = st.columns(3)
    m1.metric("Expected next week", f"{next_week} reports", help=f"Likely between {next_low} and {next_high}.")
    m2.metric("Expected in the next 4 weeks", f"{month_total} reports",
              help=f"Likely between {month_low} and {month_high}.")
    short = ("Big rise" if change >= 0.15 else "Small rise" if change > 0.03
             else "Falling" if change < -0.03 else "No real change")
    m3.metric("Compared with the last 4 weeks", short, help=f"{change:+.0%} on the last 4 weeks.")

    # main chart: history, forecast, likely range, and a "today" line
    hist = history.assign(series="Reports received", value=history["actual"])
    joined = forecast[forecast["forecast"].notna()].assign(series="Forecast", value=lambda d: d["forecast"])
    lines = pd.concat([hist, joined])[["week_start", "series", "value"]]
    lines["week"] = lines["week_start"].map(day_month)
    color = alt.Color("series:N", title=None,
                      scale=alt.Scale(domain=["Reports received", "Forecast"],
                                      range=[COLOR_ACTUAL, COLOR_FORECAST]),
                      legend=alt.Legend(orient="top", labelFontSize=13))
    base = alt.Chart(lines).encode(
        x=alt.X("week_start:T", title=None, axis=alt.Axis(format="%b %Y", labelFontSize=12)),
        y=alt.Y("value:Q", title="Reports per week", scale=alt.Scale(zero=True)),
    )
    chart = base.mark_line(strokeWidth=2.5).encode(
        color=color,
        strokeDash=alt.condition(alt.datum.series == "Forecast", alt.value([6, 4]), alt.value([1, 0])),
        tooltip=[alt.Tooltip("week:N", title="Week starting"), alt.Tooltip("series:N", title=""),
                 alt.Tooltip("value:Q", title="Reports", format=".0f")],
    )
    layers = [chart, base.mark_point(size=30, filled=True).encode(color=color, tooltip=[
        alt.Tooltip("week:N", title="Week starting"), alt.Tooltip("value:Q", title="Reports", format=".0f")])]
    if weeks_ahead is not None:
        band = weeks_ahead.assign(week_start=pd.to_datetime(weeks_ahead["week_start"]))
        layers.insert(0, alt.Chart(band).mark_area(opacity=0.18, color=COLOR_FORECAST).encode(
            x="week_start:T", y="likely_low:Q", y2="likely_high:Q"))
    today = pd.DataFrame({"week_start": [last_week], "label": ["Last full week of data"]})
    layers.append(alt.Chart(today).mark_rule(strokeDash=[2, 3], color="#718096").encode(x="week_start:T"))
    layers.append(alt.Chart(today).mark_text(align="left", dx=4, dy=-6, color="#4a5568", fontSize=11)
                  .encode(x="week_start:T", y=alt.value(12), text="label:N"))
    st.altair_chart(alt.layer(*layers).properties(height=340), width="stretch")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**What this means**")
        points = [f"Expect about **{next_week} reports a week**, {change_words(change)}."]
        if watch is not None and watch["change"] > 0.03:
            points.append(f"**{problem(watch['category'])}** is the one problem type going up: "
                          f"from about {watch['recent']:.0f} to {watch['expected']:.0f} reports a week.")
        if len(history):
            peak = history.loc[history["actual"].idxmax()]
            ratio = peak["actual"] / history["actual"].median()
            points.append(f"The busiest week of the year was **{day_month(peak['week_start'])} "
                          f"{pd.Timestamp(peak['week_start']):%Y}** with {peak['actual']:.0f} reports, "
                          f"{ratio:.1f} times a normal week.")
        metrics_text = read_text(FORECAST_METRICS)
        if metrics_text:
            metrics = json.loads(metrics_text)
            error = metrics["mae_by_model"][metrics["selected_model"]]
            points.append("When we tested the forecast on past weeks, it was usually within "
                          f"**about {error:.0f} reports a week** of what really happened.")
        st.markdown("\n".join(f"- {p}" for p in points))
        if weeks_ahead is not None:
            table = pd.DataFrame({
                "Week starting": [day_month(w) for w in weeks_ahead["week_start"]],
                "Reports expected": weeks_ahead["expected_reports"].astype(int),
                "Likely range": [f"{lo} to {hi}" for lo, hi in
                                 zip(weeks_ahead["likely_low"], weeks_ahead["likely_high"])],
            })
            st.dataframe(table, hide_index=True, width="stretch")
    with right:
        if by_cat is not None:
            options = list(trends["category"])  # rising problem types first
            cat = st.selectbox("Look at one type of problem", options, format_func=problem)
            part = by_cat[by_cat["category"] == cat]
            part = part[part["week_start"] >= part["week_start"].max() - pd.Timedelta(weeks=30)]
            long = pd.concat([
                part.dropna(subset=["actual"]).assign(series="Reports received", value=lambda d: d["actual"]),
                part.dropna(subset=["forecast"]).assign(series="Forecast", value=lambda d: d["forecast"]),
            ])
            long["week"] = long["week_start"].map(day_month)
            cat_chart = alt.Chart(long).mark_line(strokeWidth=2, point=True).encode(
                x=alt.X("week_start:T", title=None, axis=alt.Axis(format="%b")),
                y=alt.Y("value:Q", title="Reports per week", scale=alt.Scale(zero=True)),
                color=color,
                strokeDash=alt.condition(alt.datum.series == "Forecast", alt.value([6, 4]), alt.value([1, 0])),
                tooltip=[alt.Tooltip("week:N", title="Week starting"),
                         alt.Tooltip("value:Q", title="Reports", format=".0f")],
            ).properties(height=260, title=f"{problem(cat)} reports per week (last 7 months)")
            st.altair_chart(cat_chart, width="stretch")
            row = trends[trends["category"] == cat].iloc[0]
            st.caption(f"{problem(cat)}: about {row['recent']:.0f} reports a week recently, "
                       f"{row['expected']:.0f} expected - {change_words(row['change'])}.")

    with st.expander("More detail from the forecast team"):
        text = read_text(FORECAST_INSIGHTS)
        st.markdown(text.split("\n## ")[0].replace("# Forecast insights", "") if text
                    else "Not built yet: run `python forecast/forecast.py`.")
        st.caption("Method: reports are counted per week; four simple models are tested on the "
                   "last 12 weeks and the most accurate one makes the forecast. See forecast/README.md.")

with tab_h:
    st.subheader("Where the problems are")
    with st.expander("How to read this page"):
        st.markdown(
            "- Reports are grouped into **5 areas** by where they were made.\n"
            "- The **bar chart** ranks the areas from busiest to quietest.\n"
            "- On the **map**, red markers are the centre of each area (click one for details) and "
            "the coloured cloud shows where reports are densest. The map needs an internet connection.\n"
            "- A quiet area is not always a problem-free area: some communities report less."
        )
    table = pd.DataFrame({
        "Area": ranked["area_name"],
        "Reports": ranked["report_count"].astype(int),
        "Share of all reports": (ranked["report_count"] / total_clustered).map(lambda s: f"{s:.0%}"),
    })
    if "dominant_category" in ranked and ranked["dominant_category"].nunique() > 1:
        table["Most common problem"] = ranked["dominant_category"].map(problem)
    if "average_urgency" in ranked:
        table["Average urgency"] = ranked["average_urgency"].map(lambda u: f"{u:.1f} out of 5")

    left, right = st.columns([1, 1])
    with left:
        bars = alt.Chart(table).mark_bar(color=COLOR_ACTUAL).encode(
            x=alt.X("Reports:Q", title="Reports in the last year"),
            y=alt.Y("Area:N", sort="-x", title=None, axis=alt.Axis(labelFontSize=13)),
            tooltip=["Area", alt.Tooltip("Reports:Q", format=","), "Share of all reports"],
        )
        labels = bars.mark_text(align="left", dx=4, color="#2d3748").encode(
            text=alt.Text("Reports:Q", format=","))
        st.altair_chart((bars + labels).properties(height=230, title="Reports per area, busiest first"),
                        width="stretch")
        st.markdown("**What this means**")
        points = []
        if len(ranked) >= 2:
            points.append(f"**{ranked['area_name'].iloc[0]}** and **{ranked['area_name'].iloc[1]}** "
                          f"produce {top_two_share:.0%} of all reports: crews and depots near them "
                          f"would cut response times the most.")
        if "dominant_category" in ranked and ranked["dominant_category"].nunique() == 1:
            points.append(f"{problem(ranked['dominant_category'].iloc[0])} is the most common problem "
                          f"in every area.")
        if "average_urgency" in ranked and ranked["average_urgency"].max() - ranked["average_urgency"].min() < 0.3:
            points.append("Urgency is about the same everywhere, so busy areas need **more** capacity, "
                          "not different priorities.")
        points.append(f"**{ranked['area_name'].iloc[-1]}** reports the least. That may mean fewer "
                      f"problems, or that people there report less; next week's fairness check will look.")
        st.markdown("\n".join(f"- {p}" for p in points))
        st.dataframe(table.style.format({"Reports": "{:,}"}), hide_index=True, width="stretch")
    with right:
        map_html = read_text(MAP_FILE)
        if map_html and not cl_ph:
            if hasattr(st, "iframe"):  # newer Streamlit; map_html is our own generated file
                st.iframe(map_html, height=520)
            else:
                import streamlit.components.v1 as components
                components.html(map_html, height=520)
            st.caption("Click a red marker for details. Blank map? It needs an internet connection; "
                       "the chart and table on the left show the same ranking.")
        else:
            st.map(clusters, latitude="latitude", longitude="longitude", size="report_count")
    with st.expander("More detail from the problem-areas team"):
        text = read_text(HOTSPOT_INSIGHTS)
        st.markdown(text.split("\n## ")[0].replace("# Hotspot insights", "") if text
                    else "Not built yet: run `python hotspots/hotspot_analysis.py`.")
        st.caption("Method: reports are grouped by location with KMeans clustering; 5 groups fitted "
                   "the data best. Each area is named after the ward most of its reports come from.")

with tab_r:
    st.subheader("Reports")
    mode = st.radio("Show", ["Urgent reports not fixed yet", "Reports that need checking by a person",
                             "All reports"], horizontal=True)
    rows = view
    if mode.startswith("Urgent"):
        rows = view[urgent & not_fixed]
    elif mode.startswith("Reports that need"):
        rows = view[view["review_required"]]
    rows = rows.sort_values(["urgency", "timestamp"], ascending=[False, False])

    if rows.empty:
        st.info("No reports match. " + ("Every report was sorted automatically."
                                        if mode.startswith("Reports that need") else
                                        "Try changing the filters on the left."))
    else:
        st.caption(f"{len(rows):,} reports, most urgent and most recent first. "
                   "Use the filters on the left to narrow them down.")
        friendly = pd.DataFrame({
            "Reported": rows["timestamp"].dt.strftime("%d %b %Y, %H:%M"),
            "Problem": rows["category"].map(problem),
            "Urgency": rows["urgency"].map(URGENCY_NAMES),
            "Area": rows["ward_or_suburb"],
            "Status": rows["status"].map(STATUS_NAMES).fillna(rows["status"]) if "status" in rows else "",
            "What the resident wrote": rows["description"],
        })
        if st.checkbox("Show why the system chose the problem type and urgency") and "reason" in rows:
            friendly["Why"] = rows["reason"]
        st.dataframe(friendly, hide_index=True, width="stretch", height=460)
    if reports_source == "classifier":
        st.caption("Problem type and urgency are chosen automatically from what the resident wrote. "
                   "Reports that are too unclear are marked for a person to check.")
