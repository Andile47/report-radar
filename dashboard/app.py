"""Report Radar - dashboard (redesigned for non-technical managers).

Run from the repo root:  streamlit run dashboard/app.py
(Build every file first with:  python run_all.py)

Four tabs, written in plain language:
  Overview       the one-screen summary: what to expect, where, and what to do
  Forecast       forecast/output.csv, projected_workload.csv, output_by_category.csv,
                 metrics.json + the "Do we have enough crews?" planner (capacity.py)
  Problem areas  hotspots/clusters.csv, hotspot_map.html
  Reports        intake/data/reports_classified.csv, falls back to data/reports.csv
                 + the "Try a report" box (try_report.py) if it exists

If a file is missing, that part shows clearly labelled example data so the
dashboard always runs while teammates finish their parts.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Optional features built by teammates: shown only if the file exists.
try:
    from capacity import show_capacity_planner
except ImportError:
    show_capacity_planner = None
try:
    from try_report import show_try_report
except ImportError:
    show_try_report = None

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
URGENCY_DOTS = {1: "⚪", 2: "🟢", 3: "🟡", 4: "🟠", 5: "🔴"}
STATUS_NAMES = {"open": "Not started", "in_progress": "Being fixed",
                "escalated": "Escalated", "resolved": "Fixed"}
URGENCY_SCALE = ("Urgency scale: 1 = cosmetic, 2 = low, 3 = medium (a service is down), "
                 "4 = high (health or safety risk), 5 = danger to life.")

# Palette
INK = "#141619"
TEAL = "#0A21C0"
AMBER = "#F2A33A"
CORAL = "#E4572E"
GREEN = "#2E9E6B"
MUTED = "#5A5D6E"
LINE = "#DADBE6"
COLOR_ACTUAL = "#2C2E3A"
COLOR_FORECAST = "#0A21C0"

st.set_page_config(page_title="Report Radar", page_icon="📡", layout="wide",
                   initial_sidebar_state="collapsed")

CSS = f"""
<style>
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1180px; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
h1, h2, h3 {{ color: {INK}; letter-spacing: -0.01em; }}

.rr-hero {{ background: linear-gradient(120deg, #050A44 0%, #0A1A8F 60%, {TEAL} 100%);
  border-radius: 22px; padding: 28px 32px; color: #fff; display: flex;
  justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 18px; }}
.rr-hero h1 {{ color: #fff; font-size: 2.3rem; margin: 2px 0 6px 0; padding: 0; }}
.rr-hero p {{ margin: 0; color: #C9CDF5; font-size: 1.05rem; }}
.rr-eyebrow {{ font-size: .75rem; letter-spacing: .12em; color: #9AA6FF; font-weight: 700; }}
.rr-chip {{ background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.28);
  padding: 6px 12px; border-radius: 999px; font-size: .8rem; white-space: nowrap; color: #fff; }}

.rr-status {{ border-radius: 18px; padding: 20px 24px; margin-bottom: 18px;
  border: 1px solid {LINE}; border-left-width: 8px; background: #fff; }}
.rr-status.ok {{ border-left-color: {GREEN}; background: #EAF6EF; }}
.rr-status.alert {{ border-left-color: {CORAL}; background: #FDEDE8; }}
.rr-status h2 {{ margin: 0 0 4px 0; padding: 0; font-size: 1.45rem; }}
.rr-status p {{ margin: 0 0 10px 0; color: {INK}; font-size: 1.02rem; }}
.rr-pill {{ display: inline-block; background: #fff; border: 1px solid {LINE}; color: {INK};
  border-radius: 999px; padding: 5px 12px; margin: 4px 8px 0 0; font-size: .9rem; }}

.rr-card {{ background: #fff; border: 1px solid {LINE}; border-radius: 18px;
  padding: 16px 18px; box-shadow: 0 1px 2px rgba(27,42,65,.05); height: 100%; }}
.rr-label {{ color: {MUTED}; font-size: .78rem; font-weight: 700; letter-spacing: .06em;
  text-transform: uppercase; }}
.rr-value {{ color: {INK}; font-size: 2.1rem; font-weight: 800; line-height: 1.2; margin: 4px 0 2px 0; }}
.rr-note {{ color: {MUTED}; font-size: .86rem; }}
.rr-card.hot .rr-value {{ color: {CORAL}; }}
.rr-card.good .rr-value {{ color: {GREEN}; }}

.rr-section {{ font-size: 1.15rem; font-weight: 700; color: {INK}; margin: 14px 0 2px 0; }}
.rr-sub {{ color: {MUTED}; font-size: .92rem; margin-bottom: 8px; }}

button[data-baseweb="tab"] {{ font-size: 1.02rem; font-weight: 600; padding: 10px 18px; }}
div[data-testid="stTabs"] > div[role="tablist"] {{ gap: 4px; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 18px; }}
div[data-testid="stExpander"] {{ border-radius: 14px; background: #fff; }}
div[data-testid="stAlert"] {{ border-radius: 14px; }}
.stButton > button {{ border-radius: 12px; font-weight: 600; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------- small HTML helpers ----------
def esc(value) -> str:
    return html.escape(str(value))


def kpi(label: str, value, note: str = "", tone: str = "") -> str:
    return (f'<div class="rr-card {tone}"><div class="rr-label">{esc(label)}</div>'
            f'<div class="rr-value">{esc(value)}</div><div class="rr-note">{esc(note)}</div></div>')


def section(title: str, sub: str = "") -> None:
    st.markdown(f'<div class="rr-section">{esc(title)}</div>'
                + (f'<div class="rr-sub">{esc(sub)}</div>' if sub else ""), unsafe_allow_html=True)


def tidy(chart):
    """One look for every chart."""
    return (chart.configure_view(strokeWidth=0)
            .configure_axis(gridColor=LINE, domainColor="#B3B4BD", tickColor="#B3B4BD",
                            labelColor=MUTED, titleColor=MUTED, labelFontSize=12, titleFontSize=12)
            .configure_legend(labelColor=INK, labelFontSize=13)
            .configure_title(color=INK, fontSize=15, anchor="start"))


# ---------- placeholder data (used only if a real file is missing) ----------
def placeholder_reports() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 300
    return pd.DataFrame(
        {
            "report_id": [f"PH-{i:04d}" for i in range(1, n + 1)],
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="14h"),
            "category": rng.choice(CATEGORIES, n),
            "description": ["Example report"] * n,
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


def change_words(value: float) -> str:
    if value >= 0.15:
        return f"a big rise ({value:.0%} more)"
    if value > 0.03:
        return f"a small rise ({value:.0%} more)"
    if value < -0.03:
        return f"a fall ({abs(value):.0%} fewer)"
    return "about the same as recent weeks"


# ---------- numbers used across the page ----------
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
surge = bool(change >= 0.15 or (len(trends) and trends["change"].max() >= 0.15))
watch = trends.iloc[0] if len(trends) else None

ranked = clusters.sort_values("report_count", ascending=False).reset_index(drop=True)
total_clustered = ranked["report_count"].sum()
top_two_share = ranked["report_count"].head(2).sum() / total_clustered if total_clustered else 0

all_urgent = reports["urgency"] >= 4
all_not_fixed = reports["status"] != "resolved" if "status" in reports else pd.Series(False, index=reports.index)
needs_check_total = int(reports["review_required"].sum())

# ---------- header ----------
st.markdown(
    '<div class="rr-hero"><div>'
    '<div class="rr-eyebrow">CITIZEN SERVICE INSIGHTS · ALEXANDRA, JOHANNESBURG</div>'
    '<h1>Report Radar</h1>'
    '<p>What residents are reporting, where it is happening, and what to expect next.</p>'
    '</div><div class="rr-chip">Demo data · not real reports</div></div>',
    unsafe_allow_html=True)

missing = [name for name, ph in [("reports", reports_source == "placeholder"),
                                 ("forecast", fc_ph), ("problem areas", cl_ph)] if ph]
if missing:
    st.warning("Some parts show EXAMPLE data because the real files aren't built yet: "
               + ", ".join(missing) + ". Run `python run_all.py` to build them.")

tab_o, tab_f, tab_h, tab_r = st.tabs(["Overview", "Forecast", "Problem areas", "Reports"])

# =====================================================================
# OVERVIEW
# =====================================================================
with tab_o:
    lines = [f"<b>Next week:</b> about {next_week} reports, {change_words(change)}.",
             f"<b>Next 4 weeks:</b> about {month_total} reports (most likely {month_low} to {month_high})."]
    if watch is not None and watch["change"] > 0.03:
        lines.append(f"<b>Keep an eye on:</b> {esc(problem(watch['category']).lower())} problems, rising from "
                     f"about {watch['recent']:.0f} to {watch['expected']:.0f} a week.")
    if len(ranked) >= 2:
        lines.append(f"<b>Busiest areas:</b> {esc(ranked['area_name'].iloc[0])} and "
                     f"{esc(ranked['area_name'].iloc[1])} ({top_two_share:.0%} of reports).")
    headline = "Plan for extra demand" if surge else "A steady month ahead"
    blurb = ("Reports are expected to rise. Check you have enough crews in the Forecast tab."
             if surge else "Current staffing should cope. Nothing is expected to spike.")
    st.markdown(
        f'<div class="rr-status {"alert" if surge else "ok"}"><h2>{headline}</h2><p>{blurb}</p>'
        + "".join(f'<span class="rr-pill">{line}</span>' for line in lines) + "</div>",
        unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(kpi("Expected next week", f"{next_week}", f"reports, likely {next_low} to {next_high}"),
                unsafe_allow_html=True)
    k2.markdown(kpi("Next 4 weeks", f"{month_total}", f"reports, likely {month_low} to {month_high}"),
                unsafe_allow_html=True)
    k3.markdown(kpi("Urgent and not fixed", f"{(all_urgent & all_not_fixed).sum():,}",
                    "need attention first", "hot" if (all_urgent & all_not_fixed).sum() else "good"),
                unsafe_allow_html=True)
    k4.markdown(kpi("Not fixed yet", f"{all_not_fixed.sum():,}", f"of {len(reports):,} reports in the last year"),
                unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([3, 2], gap="large")
    with left:
        section("Reports per week: past and expected",
                "Dark grey is what happened. Blue is what we expect. The shaded band is the likely range.")
        hist = history.assign(series="Reports received", value=history["actual"])
        joined = forecast[forecast["forecast"].notna()].assign(series="Forecast", value=lambda d: d["forecast"])
        lines_df = pd.concat([hist, joined])[["week_start", "series", "value"]]
        lines_df["week"] = lines_df["week_start"].map(day_month)
        color = alt.Color("series:N", title=None,
                          scale=alt.Scale(domain=["Reports received", "Forecast"],
                                          range=[COLOR_ACTUAL, COLOR_FORECAST]),
                          legend=alt.Legend(orient="top"))
        base = alt.Chart(lines_df).encode(
            x=alt.X("week_start:T", title=None, axis=alt.Axis(format="%b %Y")),
            y=alt.Y("value:Q", title="Reports per week", scale=alt.Scale(zero=True)),
        )
        line = base.mark_line(strokeWidth=3).encode(
            color=color,
            strokeDash=alt.condition(alt.datum.series == "Forecast", alt.value([6, 4]), alt.value([1, 0])),
            tooltip=[alt.Tooltip("week:N", title="Week starting"), alt.Tooltip("series:N", title=""),
                     alt.Tooltip("value:Q", title="Reports", format=".0f")])
        layers = [line]
        if weeks_ahead is not None:
            band = weeks_ahead.assign(week_start=pd.to_datetime(weeks_ahead["week_start"]))
            layers.insert(0, alt.Chart(band).mark_area(opacity=0.2, color=COLOR_FORECAST).encode(
                x="week_start:T", y="likely_low:Q", y2="likely_high:Q"))
        today = pd.DataFrame({"week_start": [last_week]})
        layers.append(alt.Chart(today).mark_rule(strokeDash=[2, 3], color="#9AA3B2").encode(x="week_start:T"))
        st.altair_chart(tidy(alt.layer(*layers).properties(height=320)), width="stretch")
        st.caption("The dotted line marks the last full week of data.")
    with right:
        section("Where reports come from", "Busiest areas first.")
        table = pd.DataFrame({"Area": ranked["area_name"], "Reports": ranked["report_count"].astype(int)})
        bars = alt.Chart(table).mark_bar(color=TEAL, cornerRadiusEnd=6, size=26).encode(
            x=alt.X("Reports:Q", title=None, axis=alt.Axis(labels=False, ticks=False, grid=False)),
            y=alt.Y("Area:N", sort="-x", title=None, axis=alt.Axis(labelFontSize=13)),
            tooltip=["Area", alt.Tooltip("Reports:Q", format=",")])
        labels = bars.mark_text(align="left", dx=5, color=INK, fontWeight="bold").encode(
            text=alt.Text("Reports:Q", format=","))
        st.altair_chart(tidy((bars + labels).properties(height=280)), width="stretch")
        if len(ranked) >= 2:
            st.caption(f"Crews near {ranked['area_name'].iloc[0]} and {ranked['area_name'].iloc[1]} "
                       "would cut response times the most.")

    with st.expander("Why can we trust these numbers?"):
        metrics_text = read_text(FORECAST_METRICS)
        if metrics_text:
            metrics = json.loads(metrics_text)
            error = metrics["mae_by_model"][metrics["selected_model"]]
            st.markdown(f"We tested the forecast on past weeks. It was usually within **about {error:.0f} "
                        "reports a week** of what really happened.")
        st.markdown("All the data in this demo is synthetic: realistic, but not real residents.")

# =====================================================================
# FORECAST
# =====================================================================
with tab_f:
    section("What is coming", "The next four weeks, in plain numbers.")
    short = ("Big rise" if change >= 0.15 else "Small rise" if change > 0.03
             else "Falling" if change < -0.03 else "No real change")
    m1, m2, m3 = st.columns(3)
    m1.markdown(kpi("Expected next week", f"{next_week}", f"likely between {next_low} and {next_high}"),
                unsafe_allow_html=True)
    m2.markdown(kpi("Expected in 4 weeks", f"{month_total}", f"likely between {month_low} and {month_high}"),
                unsafe_allow_html=True)
    m3.markdown(kpi("Compared with the last 4 weeks", short, f"{change:+.0%} on the last 4 weeks",
                    "hot" if change >= 0.15 else ""), unsafe_allow_html=True)
    st.write("")

    left, right = st.columns([1, 1], gap="large")
    with left:
        section("Week by week")
        if weeks_ahead is not None:
            wk = pd.DataFrame({
                "Week starting": [day_month(w) for w in weeks_ahead["week_start"]],
                "Reports expected": weeks_ahead["expected_reports"].astype(int),
                "Likely range": [f"{lo} to {hi}" for lo, hi in
                                 zip(weeks_ahead["likely_low"], weeks_ahead["likely_high"])],
            })
            st.dataframe(wk, hide_index=True, width="stretch")
        if len(history):
            peak = history.loc[history["actual"].idxmax()]
            ratio = peak["actual"] / history["actual"].median()
            st.caption(f"The busiest week of the year was {day_month(peak['week_start'])} "
                       f"{pd.Timestamp(peak['week_start']):%Y}, with {peak['actual']:.0f} reports "
                       f"({ratio:.1f} times a normal week).")
    with right:
        section("By type of problem")
        if by_cat is not None:
            options = list(trends["category"])
            cat = st.selectbox("Pick a type of problem", options, format_func=problem,
                               label_visibility="collapsed")
            part = by_cat[by_cat["category"] == cat]
            part = part[part["week_start"] >= part["week_start"].max() - pd.Timedelta(weeks=30)]
            long = pd.concat([
                part.dropna(subset=["actual"]).assign(series="Reports received", value=lambda d: d["actual"]),
                part.dropna(subset=["forecast"]).assign(series="Forecast", value=lambda d: d["forecast"]),
            ])
            long["week"] = long["week_start"].map(day_month)
            ccolor = alt.Color("series:N", title=None,
                               scale=alt.Scale(domain=["Reports received", "Forecast"],
                                               range=[COLOR_ACTUAL, COLOR_FORECAST]),
                               legend=alt.Legend(orient="top"))
            cat_chart = alt.Chart(long).mark_line(strokeWidth=2.5, point=True).encode(
                x=alt.X("week_start:T", title=None, axis=alt.Axis(format="%b")),
                y=alt.Y("value:Q", title="Reports per week", scale=alt.Scale(zero=True)),
                color=ccolor,
                strokeDash=alt.condition(alt.datum.series == "Forecast", alt.value([6, 4]), alt.value([1, 0])),
                tooltip=[alt.Tooltip("week:N", title="Week starting"),
                         alt.Tooltip("value:Q", title="Reports", format=".0f")],
            ).properties(height=230)
            st.altair_chart(tidy(cat_chart), width="stretch")
            row = trends[trends["category"] == cat].iloc[0]
            st.caption(f"{problem(cat)}: about {row['recent']:.0f} reports a week recently, "
                       f"{row['expected']:.0f} expected, {change_words(row['change'])}.")
        else:
            st.info("The per-problem forecast isn't built yet: run `python run_all.py`.")

    if show_capacity_planner is not None:
        show_capacity_planner()

    with st.expander("How the forecast works"):
        text = read_text(FORECAST_INSIGHTS)
        st.markdown(text.split("\n## ")[0].replace("# Forecast insights", "") if text
                    else "Not built yet: run `python forecast/forecast.py`.")
        st.caption("Reports are counted per week. Four simple models are tested on the last 12 weeks "
                   "and the most accurate one makes the forecast. See forecast/README.md.")

# =====================================================================
# PROBLEM AREAS
# =====================================================================
with tab_h:
    section("Where the problems are",
            "Reports are grouped into 5 areas by where they were made.")
    table = pd.DataFrame({
        "Area": ranked["area_name"],
        "Reports": ranked["report_count"].astype(int),
        "Share of all reports": (ranked["report_count"] / total_clustered).map(lambda s: f"{s:.0%}"),
    })
    if "dominant_category" in ranked and ranked["dominant_category"].nunique() > 1:
        table["Most common problem"] = ranked["dominant_category"].map(problem)
    if "average_urgency" in ranked:
        table["Average urgency"] = ranked["average_urgency"].map(lambda u: f"{u:.1f} out of 5")

    left, right = st.columns([1, 1], gap="large")
    with left:
        bars = alt.Chart(table).mark_bar(color=TEAL, cornerRadiusEnd=6, size=28).encode(
            x=alt.X("Reports:Q", title="Reports in the last year"),
            y=alt.Y("Area:N", sort="-x", title=None, axis=alt.Axis(labelFontSize=13)),
            tooltip=["Area", alt.Tooltip("Reports:Q", format=","), "Share of all reports"])
        labels = bars.mark_text(align="left", dx=5, color=INK, fontWeight="bold").encode(
            text=alt.Text("Reports:Q", format=","))
        st.altair_chart(tidy((bars + labels).properties(height=240)), width="stretch")

        points = []
        if len(ranked) >= 2:
            points.append(f"**{ranked['area_name'].iloc[0]}** and **{ranked['area_name'].iloc[1]}** "
                          f"produce {top_two_share:.0%} of all reports. Crews and depots near them "
                          f"would cut response times the most.")
        if "dominant_category" in ranked and ranked["dominant_category"].nunique() == 1:
            points.append(f"{problem(ranked['dominant_category'].iloc[0])} is the most common problem "
                          f"in every area.")
        if "average_urgency" in ranked and ranked["average_urgency"].max() - ranked["average_urgency"].min() < 0.3:
            points.append("Urgency is about the same everywhere, so busy areas need **more** capacity, "
                          "not different priorities.")
        points.append(f"**{ranked['area_name'].iloc[-1]}** reports the least. That may mean fewer "
                      f"problems, or that people there report less.")
        with st.container(border=True):
            st.markdown("**What this means**")
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
                       "the chart and table show the same ranking.")
        else:
            st.map(clusters, latitude="latitude", longitude="longitude", size="report_count")
    with st.expander("How the areas were found"):
        text = read_text(HOTSPOT_INSIGHTS)
        st.markdown(text.split("\n## ")[0].replace("# Hotspot insights", "") if text
                    else "Not built yet: run `python hotspots/hotspot_analysis.py`.")
        st.caption("Reports are grouped by location with KMeans clustering; 5 groups fitted the data "
                   "best. Each area is named after the ward most of its reports come from.")

# =====================================================================
# REPORTS
# =====================================================================
with tab_r:
    if show_try_report is not None:
        show_try_report()
        st.divider()

    section("Browse reports", "Use the filters to narrow the list. They only affect this tab.")
    codes = sorted(reports["category"].dropna().unique(), key=lambda c: problem(c))
    wards = sorted(reports["ward_or_suburb"].dropna().unique())
    st.caption("Tap to narrow the list. Leave a row empty to show everything.")
    picked = st.pills("Type of problem", codes, selection_mode="multi", format_func=problem)
    picked_wards = st.pills("Area", wards, selection_mode="multi")
    f3, f4 = st.columns(2)
    min_urg = f3.select_slider("Urgency of at least", options=[1, 2, 3, 4, 5], value=1,
                               format_func=lambda u: URGENCY_NAMES[u])
    search = f4.text_input("Search what residents wrote", placeholder="e.g. pothole")
    chosen = picked or codes
    chosen_wards = picked_wards or wards

    view = reports[reports["category"].isin(chosen)
                   & reports["ward_or_suburb"].isin(chosen_wards)
                   & (reports["urgency"] >= min_urg)]
    if search:
        view = view[view["description"].str.contains(search, case=False, na=False)]
    not_fixed = view["status"] != "resolved" if "status" in view else pd.Series(False, index=view.index)
    urgent = view["urgency"] >= 4

    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi("Matching reports", f"{len(view):,}", "after your filters"), unsafe_allow_html=True)
    c2.markdown(kpi("Urgent and not fixed", f"{(urgent & not_fixed).sum():,}", "need attention first",
                    "hot" if (urgent & not_fixed).sum() else "good"), unsafe_allow_html=True)
    c3.markdown(kpi("Need a person to check", f"{int(view['review_required'].sum()):,}",
                    "too unclear to sort automatically"), unsafe_allow_html=True)
    st.write("")

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
                                        "Try changing the filters above."))
    else:
        st.caption(f"{len(rows):,} reports, most urgent and most recent first.")
        friendly = pd.DataFrame({
            "Reported": rows["timestamp"].dt.strftime("%d %b %Y, %H:%M"),
            "Problem": rows["category"].map(problem),
            "Urgency": rows["urgency"].map(lambda u: f"{URGENCY_DOTS.get(u, '')} {URGENCY_NAMES.get(u, u)}"),
            "Area": rows["ward_or_suburb"],
            "Status": rows["status"].map(STATUS_NAMES).fillna(rows["status"]) if "status" in rows else "",
            "What the resident wrote": rows["description"],
        })
        if st.checkbox("Show why the system chose the problem type and urgency") and "reason" in rows:
            friendly["Why"] = rows["reason"]
        st.dataframe(friendly, hide_index=True, width="stretch", height=460)
    st.caption(URGENCY_SCALE)
    if reports_source == "classifier":
        st.caption("Problem type and urgency are chosen automatically from what the resident wrote. "
                   "Reports that are too unclear are marked for a person to check.")
