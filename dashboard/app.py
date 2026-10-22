"""Report Radar - Week 5 dashboard (starter).

Run from the repo root:  streamlit run dashboard/app.py

Reads three files. If one is missing, it shows clearly labelled placeholder
data so the dashboard always runs while teammates finish their parts.

  data/reports.csv        (Role 1 + Role 4)
      report_id, timestamp, category, description, ward_or_suburb,
      latitude, longitude, urgency, status, hours_to_resolve
  forecast/output.csv     (Role 2)
      week_start, actual, forecast
  hotspots/clusters.csv   (Role 3)
      cluster, area_name, report_count, latitude, longitude
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
REPORTS_FILE = ROOT / "data" / "reports.csv"
FORECAST_FILE = ROOT / "forecast" / "output.csv"
CLUSTERS_FILE = ROOT / "hotspots" / "clusters.csv"

st.set_page_config(page_title="Report Radar", layout="wide")


# ---------- placeholder data (used only if a real file is missing) ----------
def placeholder_reports() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 300
    return pd.DataFrame(
        {
            "report_id": range(1, n + 1),
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="14h"),
            "category": rng.choice(["water", "roads", "electricity", "waste"], n),
            "description": ["Placeholder report"] * n,
            "ward_or_suburb": rng.choice(["Ward A", "Ward B", "Ward C"], n),
            "latitude": -26.2 + rng.normal(0, 0.05, n),
            "longitude": 28.04 + rng.normal(0, 0.05, n),
            "urgency": rng.integers(1, 6, n),
            "status": rng.choice(["open", "in progress", "resolved"], n),
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
            "cluster": [0, 1, 2, 3, 4],
            "area_name": ["Area 1", "Area 2", "Area 3", "Area 4", "Area 5"],
            "report_count": [120, 95, 70, 50, 30],
            "latitude": [-26.20, -26.15, -26.25, -26.18, -26.23],
            "longitude": [28.04, 28.10, 28.00, 27.95, 28.08],
        }
    )


@st.cache_data
def load(path: Path, _fallback, date_cols=()):
    """Return (dataframe, is_placeholder)."""
    if path.exists():
        return pd.read_csv(path, parse_dates=list(date_cols)), False
    return _fallback(), True


reports, rep_ph = load(REPORTS_FILE, placeholder_reports, ["timestamp"])
forecast, fc_ph = load(FORECAST_FILE, placeholder_forecast, ["week_start"])
clusters, cl_ph = load(CLUSTERS_FILE, placeholder_clusters)

# ---------- header ----------
st.title("Report Radar")
st.caption("Week 5: Predictive insights. When will reports surge, and where?")

missing = [
    name
    for name, ph in [("reports", rep_ph), ("forecast", fc_ph), ("hotspots", cl_ph)]
    if ph
]
if missing:
    st.warning(
        "Showing PLACEHOLDER data for: "
        + ", ".join(missing)
        + ". These will switch to real data automatically once the files exist."
    )

# ---------- sidebar filters (apply to the reports tab and the metrics) ----------
st.sidebar.header("Filters")
cats = sorted(reports["category"].dropna().unique())
chosen = st.sidebar.multiselect("Category", cats, default=cats)
min_urg = st.sidebar.slider("Minimum urgency", 1, 5, 1)
view = reports[reports["category"].isin(chosen) & (reports["urgency"] >= min_urg)]

# ---------- headline numbers ----------
c1, c2, c3 = st.columns(3)
c1.metric("Reports", f"{len(view):,}")
c2.metric("Average urgency", f"{view['urgency'].mean():.1f}" if len(view) else "-")
c3.metric("High urgency (4-5)", f"{(view['urgency'] >= 4).sum():,}")

# ---------- tabs ----------
tab_f, tab_h, tab_r = st.tabs(["Forecast", "Hotspots", "Reports"])

with tab_f:
    st.subheader("Projected workload")
    st.line_chart(forecast.set_index("week_start")[["actual", "forecast"]])
    st.info("TODO (Role 2): add 2-3 sentences on what the forecast says.")

with tab_h:
    st.subheader("Hotspots")
    left, right = st.columns([2, 1])
    left.map(clusters, latitude="latitude", longitude="longitude", size="report_count")
    ranked = clusters.sort_values("report_count", ascending=False)
    right.dataframe(ranked[["area_name", "report_count"]], hide_index=True)
    st.info("TODO (Role 3): add 2-3 sentences on what the map shows.")

with tab_r:
    st.subheader("Classified reports")
    st.dataframe(
        view[["timestamp", "category", "urgency", "ward_or_suburb", "description"]],
        hide_index=True,
    )
