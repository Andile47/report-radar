"""Group municipal reports by location and create a ranked interactive map."""

from __future__ import annotations

from html import escape
from pathlib import Path
import sys

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

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
K_CHECK_FILE = OUTPUT_DIR / "cluster_count_check.csv"
K_CHART_FILE = OUTPUT_DIR / "cluster_count_check.png"
INSIGHTS_FILE = OUTPUT_DIR / "insights.md"
JOHANNESBURG = [-26.2041, 28.0473]
MAP_ZOOM = 14  # close enough to see the Alexandra wards

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
    """Create the map, centred on the reports, and show density as a heat layer."""
    centre = [reports["latitude"].mean(), reports["longitude"].mean()] if not reports.empty else JOHANNESBURG
    map_view = folium.Map(location=centre, zoom_start=MAP_ZOOM, control_scale=True)
    add_map_heading(map_view)
    if not reports.empty:
        HeatMap(
            reports[["latitude", "longitude"]].values.tolist(),
            name="Report concentration",
            radius=18,
            blur=14,
            min_opacity=0.25,
        ).add_to(map_view)

        points_layer = folium.FeatureGroup(name="Individual reports", show=False)
        point_cluster = MarkerCluster().add_to(points_layer)
        for _, report in reports.iterrows():
            report_id = escape(str(report.get("report_id", "Report")))
            category = escape(str(report.get("category", "Unknown")))
            folium.CircleMarker(
                location=[report["latitude"], report["longitude"]],
                radius=3,
                color="#245b75",
                fill=True,
                fill_opacity=0.7,
                popup=(
                    f"{report_id}<br>Category: {category}<br>"
                    f"Cluster: {report['cluster_id']}"
                ),
            ).add_to(point_cluster)
        points_layer.add_to(map_view)

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


def choose_cluster_count(reports: pd.DataFrame, k_values=range(2, 11)) -> pd.DataFrame:
    """Help choose the number of clusters. For each k, record:
    * inertia (elbow method): how spread out the points are inside their
      clusters. It always falls as k grows; look for the "elbow" where
      adding more clusters stops helping much.
    * silhouette score: how well each point fits its own cluster compared
      with the next-nearest one (-1 to 1, higher is better).
    A sample of 2,000 points keeps the silhouette quick to calculate."""
    coordinates = reports[["latitude", "longitude"]].to_numpy()
    rows = []
    for k in k_values:
        if k >= len(coordinates):
            break
        model = KMeans(n_clusters=k, random_state=42, n_init=10).fit(coordinates)
        silhouette = silhouette_score(
            coordinates, model.labels_, sample_size=min(2000, len(coordinates)), random_state=42
        )
        rows.append({"k": k, "inertia": model.inertia_, "silhouette": round(float(silhouette), 3)})
    return pd.DataFrame(rows)


def plot_cluster_count(check: pd.DataFrame, chosen: int) -> None:
    """Save the elbow and silhouette charts side by side."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.8))
    left.plot(check["k"], check["inertia"], marker="o", color="#2b6cb0")
    left.set_title("Elbow method (lower = tighter clusters)")
    left.set_xlabel("Number of clusters (k)")
    left.set_ylabel("Inertia")
    right.plot(check["k"], check["silhouette"], marker="o", color="#2f855a")
    right.set_title("Silhouette score (higher = better separated)")
    right.set_xlabel("Number of clusters (k)")
    for ax in (left, right):
        ax.axvline(chosen, color="#e53e3e", linestyle="--", linewidth=1, label=f"chosen k = {chosen}")
        ax.grid(alpha=0.3)
        ax.legend()
    fig.tight_layout()
    fig.savefig(K_CHART_FILE, dpi=130)
    plt.close(fig)


def write_insights(reports: pd.DataFrame, clusters: pd.DataFrame, check: pd.DataFrame) -> str:
    """Two or three plain sentences on what the map tells the municipality."""
    total = int(clusters["report_count"].sum())
    top = clusters.iloc[:2]
    top_share = top["report_count"].sum() / total
    quietest = clusters.iloc[-1]
    urgent = clusters.sort_values("average_urgency", ascending=False).iloc[0]
    named = set(clusters["dominant_ward_or_suburb"])
    unnamed = sorted(set(reports["ward_or_suburb"].dropna()) - named) if "ward_or_suburb" in reports else []
    best_k = int(check.loc[check["silhouette"].idxmax(), "k"]) if not check.empty else len(clusters)

    urgency_range = clusters["average_urgency"].max() - clusters["average_urgency"].min()
    same_problem = (clusters["dominant_category"] == clusters.iloc[0]["dominant_category"]).all()
    sentences = [
        f"Reports are concentrated in two hotspots: {top.iloc[0]['area_name']} "
        f"({int(top.iloc[0]['report_count']):,} reports) and {top.iloc[1]['area_name']} "
        f"({int(top.iloc[1]['report_count']):,}) together account for {top_share:.0%} of all "
        f"{total:,} reports, so placing field teams and depots near them will cut response "
        f"times the most, while {quietest['area_name']} is the quietest "
        f"({int(quietest['report_count']):,} reports)."
    ]
    problem = (f"{str(clusters.iloc[0]['dominant_category']).capitalize()} is the most common "
               f"problem in every hotspot" if same_problem
               else "The most common problem differs between hotspots")
    if urgency_range < 0.3:
        sentences.append(f"{problem}, and average urgency is similar everywhere "
                         f"({clusters['average_urgency'].min():.1f} to "
                         f"{clusters['average_urgency'].max():.1f} out of 5), so the busiest "
                         f"areas need more capacity rather than different priorities.")
    else:
        sentences.append(f"{problem}; {urgent['area_name']} has the most urgent reports on "
                         f"average ({urgent['average_urgency']:.1f} out of 5).")
    sentences.append(
        "Fewer reports does not have to mean fewer problems: quieter areas may simply report "
        "less, which the Week 6 fairness check should look at"
        + (f" ({', '.join(unnamed)} has no hotspot of its own because its reports fall inside "
           f"neighbouring clusters)." if unnamed else "."))
    text = " ".join(sentences)

    table = ["| Rank | Area | Reports | Main problem | Average urgency |",
             "| --- | --- | --- | --- | --- |"]
    for row in clusters.itertuples():
        table.append(f"| {row.rank} | {row.area_name} | {row.report_count:,} | "
                     f"{row.dominant_category} | {row.average_urgency:.1f} |")
    INSIGHTS_FILE.write_text(
        "# Hotspot insights\n\n" + text + "\n\n## Ranked hotspots (busiest first)\n\n"
        + "\n".join(table) + f"\n\nNumber of clusters: {len(clusters)}. The silhouette score "
        f"was highest at k = {best_k} (see cluster_count_check.png).\n"
    )
    return text


def write_empty_outputs(message: str) -> None:
    """Write empty result tables and an explanatory map when no points exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=CLUSTER_COLUMNS).to_csv(CLUSTERS_FILE, index=False)
    pd.DataFrame().to_csv(REPORTS_FILE, index=False)
    map_view = folium.Map(location=JOHANNESBURG, zoom_start=11, control_scale=True)
    add_map_heading(map_view)
    folium.Marker(JOHANNESBURG, popup=message).add_to(map_view)
    map_view.save(MAP_FILE)


def analyze() -> int:
    """Analyze reports and save hotspot outputs."""
    if FOLIUM_IMPORT_ERROR is not None:
        print("Error: Folium is required to create the hotspot map.")
        print("Install dependencies with: python -m pip install -r requirements.txt")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    reports = load_reports()
    if reports is None:
        return 1

    print(f"Dataset: {DATA_FILE}")
    print("Note: project reports are synthetic; hotspot results are simulated.")
    print(f"Total reports loaded: {len(reports):,}")
    coordinate_reports = valid_coordinate_reports(reports)
    if coordinate_reports is None:
        return 1
    if coordinate_reports.empty:
        print("No usable coordinates; saving empty analysis files and a Johannesburg map.")
        write_empty_outputs("No reports with usable coordinates were found.")
        return 0

    clustered_reports, model, _ = assign_clusters(coordinate_reports)
    clusters = rank_clusters(summarize_clusters(clustered_reports, model))
    clustered_reports.to_csv(REPORTS_FILE, index=False)
    clusters.to_csv(CLUSTERS_FILE, index=False)
    build_map(clustered_reports, clusters)
    check = choose_cluster_count(coordinate_reports)
    check.to_csv(K_CHECK_FILE, index=False)
    if not check.empty:
        plot_cluster_count(check, len(clusters))
    insights = write_insights(coordinate_reports, clusters, check)

    print("\nRanked hotspots (reported issue concentrations; not causal or predictive):")
    for _, cluster in clusters.iterrows():
        print(
            f"  #{int(cluster['rank'])}: {int(cluster['report_count'])} reports | "
            f"{cluster['dominant_ward_or_suburb']} | {cluster['dominant_category']}"
        )
    print(f"Saved: {CLUSTERS_FILE}")
    print(f"Saved: {REPORTS_FILE}")
    print(f"Saved: {MAP_FILE}")
    print("\nChoosing the number of clusters (higher silhouette = better):")
    for row in check.itertuples():
        print(f"  k={row.k:<2} silhouette {row.silhouette:.3f}")
    print(f"Saved: {K_CHECK_FILE}")
    print(f"Saved: {INSIGHTS_FILE}")
    print("\n" + insights)
    return 0


if __name__ == "__main__":
    sys.exit(analyze())
