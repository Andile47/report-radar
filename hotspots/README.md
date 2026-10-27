# Hotspot Analysis

This module groups the locations of municipal reports into geographic concentrations and ranks those groups by report count. The clusters describe where reports in this dataset are concentrated; they do not establish why an issue occurred or predict future problems. The repository describes its municipal reports as synthetic, so all findings from this input are simulated, not verified real incidents.

## How it works

The script reads `data/reports.csv` with pandas and checks that latitude and longitude are present, numeric, and within valid geographic ranges. Records with missing or invalid coordinates are excluded from clustering and counted in the terminal output. KMeans then groups the remaining latitude/longitude pairs. Because nearby coordinates tend to represent nearby locations, these fields give the model a simple geographic representation; they are not administrative boundaries.

The script uses five clusters. If fewer than five records have usable coordinates, it uses one cluster per valid record instead. `random_state=42` and `n_init=10` make the model's initialization repeatable and improve the chance of finding a good grouping.

### Choosing the number of clusters

KMeans needs to be told how many clusters to make, so the script tests every value from 2 to 10 with two standard checks and saves them to `cluster_count_check.csv` and `cluster_count_check.png`:

- **Elbow method:** inertia measures how spread out the reports are inside their clusters. It always falls as clusters are added; the "elbow" is where adding more stops helping much. Here the drop flattens after 5 to 6 clusters.
- **Silhouette score:** how well each report fits its own cluster compared with the next-nearest one, from -1 to 1, higher is better. It peaks at **k = 5 (0.501)**, ahead of k = 4 (0.487) and k = 6 (0.451).

Both point to 5, so five clusters is supported by the data, not just a convenient number.

Clusters are sorted from highest to lowest report count. The summary includes each centre, its most frequently reported suburb or ward and category, and average urgency when that field is available. A high count can reflect reporting behavior or data collection patterns; it is not proof of a higher underlying incident rate.

## Outputs

- `clusters.csv`: one row per cluster, ranked by report count. Includes cluster ID, report count, centre latitude/longitude, dominant suburb/ward, dominant category, and average urgency. The `cluster`, `area_name`, `latitude`, and `longitude` columns are compatibility aliases for the current dashboard.
- `clustered_reports.csv`: every report with usable coordinates and its assigned cluster ID. Invalid-coordinate records are excluded.
- `hotspot_map.html`: an interactive map, centred on Alexandra, with hotspot-centre markers, a report heatmap, layer controls, and an optional layer of individual reports.
- `insights.md`: two to three sentences on what the map tells the municipality, plus the ranked list. The dashboard shows this text under "More detail" on the Problem areas tab.
- `cluster_count_check.csv` / `.png`: elbow and silhouette scores for 2 to 10 clusters.

## What the map shows

Reports are concentrated in two hotspots: Old Alexandra (1,401 reports) and East Bank (1,037) together account for 61% of all 3,994 reports, so placing field teams and depots near them will cut response times the most, while Tsutsumani is the quietest (236). Water is the most common problem in every hotspot, and average urgency is similar everywhere (3.0 to 3.1 out of 5), so the busiest areas need more capacity rather than different priorities. Quieter areas may simply report less, which the Week 6 fairness check should look at; Pan Africa has no hotspot of its own because its reports fall inside neighbouring clusters.

**Check against the data:** the two busiest hotspots match the two wards the Data Lead made report about twice as often (Old Alexandra and East Bank).

## Install and run

From the repository root, install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

Then run:

```powershell
python hotspots/hotspot_analysis.py
```

It takes about 10 seconds, most of it the cluster-count check.

The input and output paths are resolved from the script location, so it can also be launched from another current directory. Open `hotspots/hotspot_map.html` in a browser after the script completes.

## Dashboard connection

The existing Streamlit dashboard reads `hotspots/clusters.csv` and expects `area_name`, `report_count`, `latitude`, and `longitude`. Those compatibility columns are included, so the Dashboard Lead can run this module before launching the dashboard and the existing hotspot table/map can read the ranked results. The richer columns remain available for a more detailed table. To embed the interactive Folium map, the dashboard can read `hotspots/hotspot_map.html` and display its HTML in the Hotspots tab; `streamlit-folium` would be an optional dependency if a live Streamlit component is preferred, but this module does not require it.

## Limitations

- KMeans requires a chosen cluster count. Five scored best on the silhouette check, but that doesn't mean exactly five natural hotspots exist.
- Coordinate clusters are geometric groupings, not ward or suburb boundaries.
- The synthetic project data does not represent verified real municipal incidents.
- High report counts may reflect reporting bias, duplicate reports, or differences in data collection.
- Clusters identify concentrations in the supplied historical reports only; they do not prove causes or guarantee future problems.