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


def analyze() -> int:
    """Analyze reports and save hotspot outputs."""
    return 0


if __name__ == "__main__":
    sys.exit(analyze())
