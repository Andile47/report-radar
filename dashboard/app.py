"""Report Radar - Week 5 dashboard (Role 5: Dashboard, Integration and Docs Lead).

Run from the repo root:  streamlit run dashboard/app.py
(Build every file first with:  python run_all.py)

Shows the team's work in three tabs:
  Forecast   forecast/output.csv, projected_workload.csv, insights.md   (Forecast Lead)
  Hotspots   hotspots/clusters.csv, hotspot_map.html, insights.md       (Hotspot Lead)
  Reports    intake/data/reports_classified.csv                         (Intake Lead)
             falls back to data/reports.csv                             (Data Lead)

If a file is missing, that part shows clearly labelled placeholder data so
the dashboard always runs while teammates finish their parts.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
REPORTS_FILE = ROOT / "data" / "reports.csv"
CLASSIFIED_FILE = ROOT / "intake" / "data" / "reports_classified.csv"
FORECAST_FILE = ROOT / "forecast" / "output.csv"
FORECAST_CATEGORY_FILE = ROOT / "forecast" / "output_by_category.csv"
WORKLOAD_FILE = ROOT / "forecast" / "projected_workload.csv"
FORECAST_INSIGHTS = ROOT / "forecast" / "insights.md"
CLUSTERS_FILE = ROOT / "hotspots" / "clusters.csv"
MAP_FILE = ROOT / "hotspots" / "hotspot_map.html"
HOTSPOT_INSIGHTS = ROOT / "hotspots" / "insights.md"

CATEGORIES = ["water", "electricity", "roads", "sanitation", "refuse", "streetlights"]

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


@st.cache_data
def load_csv(path: Path, date_cols=()):
    return pd.read_csv(path, parse_dates=list(date_cols)) if path.exists() else None


def read_text(path: Path) -> str | None:
    return path.read_text() if path.exists() else None


def insight_paragraph(path: Path) -> str | None:
    """The sentences at the top of an insights.md file (before the first table)."""
    text = read_text(path)
    if not text:
        return None
    body = text.split("\n## ")[0]
    return "\n".join(line for line in body.splitlines() if not line.startswith("# ")).strip()


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


reports, reports_source = load_reports()
forecast = load_csv(FORECAST_FILE, ["week_start"])
fc_ph = forecast is None
forecast = placeholder_forecast() if fc_ph else forecast
clusters = load_csv(CLUSTERS_FILE)
cl_ph = clusters is None
clusters = placeholder_clusters() if cl_ph else clusters

# ---------- header ----------
st.title("Report Radar")
st.caption("Week 5: Predictive insights. When will citizen reports surge, and where? "
           "All data is synthetic.")

missing = [name for name, ph in [("reports", reports_source == "placeholder"),
                                 ("forecast", fc_ph), ("hotspots", cl_ph)] if ph]
if missing:
    st.warning("Showing PLACEHOLDER data for: " + ", ".join(missing)
               + ". Run `python run_all.py` to build the real files.")

forecast_text = insight_paragraph(FORECAST_INSIGHTS)
if forecast_text and "Surge alert" in forecast_text:
    st.error("Surge alert: see the Forecast tab.")

# ---------- sidebar filters (apply to the headline numbers and the Reports tab) ----------
st.sidebar.header("Filters")
st.sidebar.caption("These filter the headline numbers and the Reports tab. "
                   "The forecast and hotspots always use all reports.")
cats = sorted(reports["category"].dropna().unique())
chosen = st.sidebar.multiselect("Category", cats, default=cats)
wards = sorted(reports["ward_or_suburb"].dropna().unique())
chosen_wards = st.sidebar.multiselect("Ward", wards, default=wards)
min_urg = st.sidebar.slider("Minimum urgency", 1, 5, 1)
review_only = st.sidebar.checkbox("Only reports that need review")
search = st.sidebar.text_input("Search descriptions")

view = reports[reports["category"].isin(chosen)
               & reports["ward_or_suburb"].isin(chosen_wards)
               & (reports["urgency"] >= min_urg)]
if review_only:
    view = view[view["review_required"]]
if search:
    view = view[view["description"].str.contains(search, case=False, na=False)]

# ---------- headline numbers ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Reports", f"{len(view):,}")
c2.metric("Average urgency", f"{view['urgency'].mean():.1f}" if len(view) else "-")
c3.metric("High urgency (4-5)", f"{(view['urgency'] >= 4).sum():,}")
c4.metric("Need review", f"{int(view['review_required'].sum()):,}")

# ---------- tabs ----------
tab_f, tab_h, tab_r = st.tabs(["Forecast", "Hotspots", "Reports"])

with tab_f:
    st.subheader("Projected workload")
    workload = load_csv(WORKLOAD_FILE)
    if workload is not None and len(workload) > 1:
        weeks = workload.iloc[:-1]
        recent = forecast["actual"].dropna().tail(len(weeks)).mean()
        expected = weeks["expected_reports"].mean()
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Next week (likely {int(weeks['likely_low'].iloc[0])}-"
                  f"{int(weeks['likely_high'].iloc[0])})",
                  f"{int(weeks['expected_reports'].iloc[0])} reports")
        m2.metric(f"Next {len(weeks)} weeks (likely {int(workload['likely_low'].iloc[-1])}-"
                  f"{int(workload['likely_high'].iloc[-1])})",
                  f"{int(workload['expected_reports'].iloc[-1])} reports")
        m3.metric(f"Change vs last {len(weeks)} weeks", f"{(expected - recent) / recent:+.0%}")

    st.line_chart(forecast.set_index("week_start")[["actual", "forecast"]],
                  y_label="Reports per week", x_label="Week starting")
    if forecast_text:
        st.markdown(forecast_text)
    else:
        st.info("Forecast insights not built yet: run `python forecast/forecast.py`.")

    if workload is not None:
        left, right = st.columns([1, 1])
        with left:
            st.markdown("**Next 4 weeks**")
            st.dataframe(
                workload.rename(columns={"week_start": "Week starting",
                                         "expected_reports": "Expected reports",
                                         "likely_low": "Likely low", "likely_high": "Likely high"}),
                hide_index=True,
            )
        by_cat = load_csv(FORECAST_CATEGORY_FILE, ["week_start"])
        if by_cat is not None:
            with right:
                cat = st.selectbox("Forecast for one category", sorted(by_cat["category"].unique()))
                part = by_cat[by_cat["category"] == cat].set_index("week_start")
                st.line_chart(part[["actual", "forecast"]].tail(20), height=220)

with tab_h:
    st.subheader("Hotspots")
    left, right = st.columns([3, 2])
    map_html = read_text(MAP_FILE)
    with left:
        if map_html and not cl_ph:
            components.html(map_html, height=520)
            st.caption("Interactive map: click a red marker for details; switch layers top right.")
        else:
            st.map(clusters, latitude="latitude", longitude="longitude", size="report_count")
    ranked = clusters.sort_values("report_count", ascending=False)
    columns = {"rank": "Rank", "area_name": "Area", "report_count": "Reports",
               "dominant_category": "Main problem", "average_urgency": "Avg urgency"}
    shown = ranked[[c for c in columns if c in ranked.columns]].rename(columns=columns)
    if "Avg urgency" in shown:
        shown["Avg urgency"] = shown["Avg urgency"].round(1)
    right.markdown("**Busiest areas first**")
    right.dataframe(shown, hide_index=True)
    hotspot_text = insight_paragraph(HOTSPOT_INSIGHTS)
    if hotspot_text:
        st.markdown(hotspot_text)
    else:
        st.info("Hotspot insights not built yet: run `python hotspots/hotspot_analysis.py`.")

with tab_r:
    st.subheader("Classified reports")
    if reports_source == "classifier":
        agree = (reports["predicted_category"] == reports["dataset_category"]).mean()
        st.caption(f"Category and urgency come from the intake classifier "
                   f"({agree:.0%} agree with the dataset labels). Reports it could not "
                   f"classify confidently are marked 'Needs review'.")
    elif reports_source == "dataset":
        st.caption("Showing the dataset's own labels: run `python intake/classifier.py` "
                   "to add the classifier's results.")
    columns = ["timestamp", "category", "urgency", "review_required", "ward_or_suburb",
               "status", "description", "reason"]
    st.dataframe(
        view[[c for c in columns if c in view.columns]]
        .sort_values("timestamp", ascending=False)
        .rename(columns={"review_required": "Needs review", "ward_or_suburb": "Ward"}),
        hide_index=True,
        height=480,
    )
