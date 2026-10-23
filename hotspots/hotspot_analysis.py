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


def analyze() -> int:
    """Analyze reports and save hotspot outputs."""
    return 0


if __name__ == "__main__":
    sys.exit(analyze())
