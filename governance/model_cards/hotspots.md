# Model card: Problem areas (hotspots)

*Report Radar · Week 6 · last reviewed 2 Nov 2026 · rules version `hotspots-2026.10`*

## What it is for

It groups reports by where they were made and ranks the areas from busiest to quietest, so managers can decide where to base crews and depots.

**Don't use it for:** deciding which communities matter most, cutting service to quiet areas, or explaining *why* problems happen.

## Data it uses

- The latitude and longitude of each of the 3,994 **synthetic** reports in `data/reports.csv`.
- The ward name, problem type and urgency are used only to describe each area afterwards.

## How it works, in plain words

1. Group the report locations into 5 clusters with KMeans, a method that puts nearby points together.
2. Count the reports in each cluster and rank them, busiest first.
3. Name each cluster after the ward most of its reports come from.

**Why 5 areas:** values from 2 to 10 were tested. Five scored best on the silhouette check, which measures how clearly separated the groups are (0.50, against 0.49 for 4 and 0.45 for 6).

## Results

| Rank | Area | Reports | Share |
| --- | --- | --- | --- |
| 1 | Old Alexandra | 1,401 | 35% |
| 2 | East Bank | 1,037 | 26% |
| 3 | Setswetla | 753 | 19% |
| 4 | Far East Bank | 567 | 14% |
| 5 | Tsutsumani | 236 | 6% |

Water is the most common problem in every area, and average urgency is about the same everywhere (3.0 to 3.1 out of 5).

## Known limits and risks

- **Feedback loop.** Ranking by report count sends crews to busy areas. Quiet areas can then get slower service, residents there may give up reporting, and they look even quieter next time. Urgent reports already wait a median of 44 hours in Tsutsumani, against 24 in Old Alexandra.
- **Quiet is not the same as fine.** An area may report less because of less airtime, less trust, or language, not fewer problems. Counts aren't adjusted for how many people live in each area.
- **Names can mislead.** Clusters are geometric groups, not ward boundaries. Pan Africa has no area of its own because its reports fall inside neighbouring clusters.
- **Five is a setting.** It scored best, but that doesn't mean exactly five natural hotspots exist.
- **Synthetic data.** The busy wards were built into the data, so the result shows the method works, not what is true in Alexandra.

## How decisions are recorded

Every run adds one row to the decision log (`governance/logs/decisions.csv`) with the ranking, the number of areas and why it was chosen. The ranked list is also saved to `hotspots/clusters.csv`. The area fairness analysis (`governance/area_fairness.md`) checks whether quieter areas wait longer.

## Who to contact

Hotspot Lead: Tshepo Tleane. Code: `hotspots/hotspot_analysis.py`. Details: `hotspots/README.md`.
