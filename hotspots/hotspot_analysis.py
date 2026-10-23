"""Group municipal reports by location and create a ranked interactive map."""

from __future__ import annotations

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


def analyze() -> int:
    """Analyze reports and save hotspot outputs."""
    return 0


if __name__ == "__main__":
    sys.exit(analyze())
