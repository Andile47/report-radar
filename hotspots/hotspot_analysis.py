"""Group municipal reports by location and create a ranked interactive map."""

from __future__ import annotations

from html import escape
from pathlib import Path
import sys

import pandas as pd
from sklearn.cluster import KMeans

try:
    import folium
    from folium.plugins import HeatMap, MarkerCluster
except ImportError as error:
    folium = None
    HeatMap = None
    MarkerCluster = None
    FOLIUM_IMPORT_ERROR = error
else:
    FOLIUM_IMPORT_ERROR = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "reports.csv"
OUTPUT_DIR = Path(__file__).resolve().parent
CLUSTERS_FILE = OUTPUT_DIR / "clusters.csv"
REPORTS_FILE = OUTPUT_DIR / "clustered_reports.csv"
MAP_FILE = OUTPUT_DIR / "hotspot_map.html"
JOHANNESBURG = [-26.2041, 28.0473]

CLUSTER_COLUMNS = [
    "rank",
    "cluster_id",
    "report_count",
    "center_latitude",
    "center_longitude",
    "dominant_ward_or_suburb",
    "dominant_category",
    "average_urgency",
    "cluster",
    "area_name",
    "latitude",
    "longitude",
]


def most_common_value(values: pd.Series) -> str:
    """Return the most common non-empty value, or a readable fallback."""
    clean_values = values.dropna().astype(str).str.strip()
    clean_values = clean_values[clean_values != ""]
    if clean_values.empty:
        return "Unknown"
    return str(clean_values.mode().iloc[0])


def load_reports() -> pd.DataFrame | None:
    """Read the shared dataset, returning None after a helpful error."""
    if not DATA_FILE.exists():
        print(f"Error: dataset not found: {DATA_FILE}")
        return None
    try:
        return pd.read_csv(DATA_FILE)
    except pd.errors.EmptyDataError:
        print(f"Error: dataset is empty and has no column headers: {DATA_FILE}")
    except (OSError, pd.errors.ParserError) as error:
        print(f"Error: could not read dataset: {error}")
    return None


def valid_coordinate_reports(reports: pd.DataFrame) -> pd.DataFrame | None:
    """Return reports with usable geographic coordinates."""
    missing_columns = [
        column for column in ("latitude", "longitude") if column not in reports.columns
    ]
    if missing_columns:
        print("Error: required coordinate column(s) missing: " + ", ".join(missing_columns))
        return None

    coordinate_reports = reports.copy()
    coordinate_reports["latitude"] = pd.to_numeric(
        coordinate_reports["latitude"], errors="coerce"
    )
    coordinate_reports["longitude"] = pd.to_numeric(
        coordinate_reports["longitude"], errors="coerce"
    )
    valid_coordinates = (
        coordinate_reports["latitude"].between(-90, 90)
        & coordinate_reports["longitude"].between(-180, 180)
    )
    valid_reports = coordinate_reports.loc[valid_coordinates].copy()
    print(f"Valid coordinate reports: {len(valid_reports):,}")
    print(f"Excluded reports (missing or invalid coordinates): {len(reports) - len(valid_reports):,}")
    return valid_reports


def assign_clusters(reports: pd.DataFrame) -> tuple[pd.DataFrame, KMeans, int]:
    """Assign each usable report to a reproducible geographic cluster."""
    cluster_count = min(5, len(reports))
    if cluster_count < 5:
        print(f"Fewer than 5 usable reports; adapting to {cluster_count} cluster(s).")
    model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    clustered_reports = reports.copy()
    coordinates = clustered_reports[["latitude", "longitude"]]
    clustered_reports["cluster_id"] = model.fit_predict(coordinates)
    print(f"Clusters created: {cluster_count}")
    return clustered_reports, model, cluster_count


def summarize_clusters(
    reports: pd.DataFrame, model: KMeans
) -> pd.DataFrame:
    """Calculate report counts, centres, dominant labels, and urgency."""
    cluster_rows = []
    for cluster_id, group in reports.groupby("cluster_id"):
        centre = model.cluster_centers_[int(cluster_id)]
        area = (
            most_common_value(group["ward_or_suburb"])
            if "ward_or_suburb" in group
            else "Unknown"
        )
        category = (
            most_common_value(group["category"])
            if "category" in group
            else "Unknown"
        )
        urgency = (
            pd.to_numeric(group["urgency"], errors="coerce").mean()
            if "urgency" in group
            else float("nan")
        )
        cluster_rows.append(
            {
                "cluster_id": int(cluster_id),
                "report_count": len(group),
                "center_latitude": float(centre[0]),
                "center_longitude": float(centre[1]),
                "dominant_ward_or_suburb": area,
                "dominant_category": category,
                "average_urgency": urgency,
            }
        )
    return pd.DataFrame(cluster_rows)


def rank_clusters(clusters: pd.DataFrame) -> pd.DataFrame:
    """Sort busiest first and add ranks plus dashboard-compatible columns."""
    ranked = clusters.sort_values(
        ["report_count", "cluster_id"], ascending=[False, True]
    ).reset_index(drop=True)
    ranked.insert(0, "rank", range(1, len(ranked) + 1))
    ranked["cluster"] = ranked["cluster_id"]
    ranked["area_name"] = ranked["dominant_ward_or_suburb"]
    ranked["latitude"] = ranked["center_latitude"]
    ranked["longitude"] = ranked["center_longitude"]
    return ranked[CLUSTER_COLUMNS]


def add_map_heading(map_view: folium.Map) -> None:
    """Label the map and clarify that these are simulated report clusters."""
    heading = """
    <div style="position: fixed; top: 12px; left: 50px; z-index: 9999;
                background: white; padding: 10px 14px; border: 1px solid #777;
                border-radius: 4px; font-family: Arial, sans-serif;">
      <strong>Community Issue Reporter: Report Hotspots</strong><br>
      <span style="font-size: 12px;">Simulated data. Report concentrations,
      not proven causes or predictions.</span>
    </div>
    """
    map_view.get_root().html.add_child(folium.Element(heading))


def build_map(reports: pd.DataFrame, clusters: pd.DataFrame) -> None:
    """Create the Johannesburg map and show report density as a heat layer."""
    map_view = folium.Map(location=JOHANNESBURG, zoom_start=11, control_scale=True)
    add_map_heading(map_view)
    if not reports.empty:
        HeatMap(
            reports[["latitude", "longitude"]].values.tolist(),
            name="Report concentration",
            radius=18,
            blur=14,
            min_opacity=0.25,
        ).add_to(map_view)

    centre_layer = folium.FeatureGroup(name="Ranked hotspot centres", show=True)
    for _, cluster in clusters.iterrows():
        urgency = cluster["average_urgency"]
        urgency_text = "Not available" if pd.isna(urgency) else f"{urgency:.2f} / 5"
        popup = (
            f"<b>Hotspot rank #{int(cluster['rank'])}</b><br>"
            f"Reports: {int(cluster['report_count'])}<br>"
            f"Most reported area: {escape(str(cluster['dominant_ward_or_suburb']))}<br>"
            f"Most common category: {escape(str(cluster['dominant_category']))}<br>"
            f"Average urgency: {urgency_text}<br><br>"
            "A concentration of reports, not evidence of cause or future problems."
        )
        folium.Marker(
            location=[cluster["center_latitude"], cluster["center_longitude"]],
            popup=folium.Popup(popup, max_width=320),
            tooltip=f"Rank #{int(cluster['rank'])}: {int(cluster['report_count'])} reports",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(centre_layer)
    centre_layer.add_to(map_view)
    folium.LayerControl(collapsed=False).add_to(map_view)
    map_view.save(MAP_FILE)


def analyze() -> int:
    """Analyze reports and save hotspot outputs."""
    return 0


if __name__ == "__main__":
    sys.exit(analyze())
