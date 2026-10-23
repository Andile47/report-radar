# Hotspot Analysis

This module groups the locations of municipal reports into geographic concentrations and ranks those groups by report count. The clusters describe where reports in this dataset are concentrated; they do not establish why an issue occurred or predict future problems. The repository describes its municipal reports as synthetic, so all findings from this input are simulated, not verified real incidents.

## How it works

The script reads `data/reports.csv` with pandas and checks that latitude and longitude are present, numeric, and within valid geographic ranges. Records with missing or invalid coordinates are excluded from clustering and counted in the terminal output. KMeans then groups the remaining latitude/longitude pairs. Because nearby coordinates tend to represent nearby locations, these fields give the model a simple geographic representation; they are not administrative boundaries.

The target is five clusters to provide a consistent, easy-to-compare summary for the project. If fewer than five records have usable coordinates, the script uses one cluster per valid record instead. `random_state=42` and `n_init=10` make the model's initialization repeatable and improve the chance of finding a good grouping.

Clusters are sorted from highest to lowest report count. The summary includes each centre, its most frequently reported suburb or ward and category, and average urgency when that field is available. A high count can reflect reporting behavior or data collection patterns; it is not proof of a higher underlying incident rate.

## Outputs

- `clusters.csv`: one row per cluster, ranked by report count. Includes cluster ID, report count, centre latitude/longitude, dominant suburb/ward, dominant category, and average urgency. The `cluster`, `area_name`, `latitude`, and `longitude` columns are compatibility aliases for the current dashboard.
- `clustered_reports.csv`: every report with usable coordinates and its assigned cluster ID. Invalid-coordinate records are excluded.
- `hotspot_map.html`: an interactive Johannesburg map with hotspot-centre markers, a report heatmap, layer controls, and an optional layer of individual reports.

## Install and run

From the repository root, install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

Then run:

```powershell
python hotspots/hotspot_analysis.py
```

The input and output paths are resolved from the script location, so it can also be launched from another current directory. Open `hotspots/hotspot_map.html` in a browser after the script completes.

## Dashboard connection

The existing Streamlit dashboard reads `hotspots/clusters.csv` and expects `area_name`, `report_count`, `latitude`, and `longitude`. Those compatibility columns are included, so the Dashboard Lead can run this module before launching the dashboard and the existing hotspot table/map can read the ranked results. The richer columns remain available for a more detailed table. To embed the interactive Folium map, the dashboard can read `hotspots/hotspot_map.html` and display its HTML in the Hotspots tab; `streamlit-folium` would be an optional dependency if a live Streamlit component is preferred, but this module does not require it.

## Limitations

- KMeans requires a chosen cluster count; five is a project setting, not a claim that exactly five natural hotspots exist.
- Coordinate clusters are geometric groupings, not ward or suburb boundaries.
- The synthetic project data does not represent verified real municipal incidents.
- High report counts may reflect reporting bias, duplicate reports, or differences in data collection.
- Clusters identify concentrations in the supplied historical reports only; they do not prove causes or guarantee future problems.