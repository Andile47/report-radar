# Report Radar: 5-minute demo script

**Before the demo:** run `python run_all.py`, then `streamlit run dashboard/app.py`, and have the dashboard open on the Forecast tab. Check the laptop has internet (the hotspot map needs it). Names marked *(confirm)* need checking against who actually presents.

| Time | Speaker | Shows | Says (about 30 seconds each, in your own words) |
| --- | --- | --- | --- |
| 0:00-0:40 | **Role 5: Dashboard Lead** — Andile Khoza *(confirm)* | Dashboard header and headline numbers | "Municipalities get thousands of reports and are always reacting. Report Radar sorts every report, predicts next month's workload and shows where problems cluster, so teams can plan ahead. This year of data is synthetic: 3,994 reports from Alexandra." |
| 0:40-1:20 | **Role 1: Data Lead** — *(confirm)* | `data/weekly_volume.png` or the Forecast chart | "We had no real reports, so we generated realistic ones: more water and road problems in summer, three surge periods, and two wards that report twice as often. You can see them here: the January peak of 132 reports was 55% water, and the June spike was mostly electricity during load-shedding." |
| 1:20-2:20 | **Role 4: Intake Lead** — petroblyn | Reports tab, then search "amanzi"; tick "Only reports that need review" | "Each report is sorted by keywords with weights, so 'pothole filled with water' counts as roads, not water. It handles typos and isiZulu, and gives a reason. On 30 deliberately tricky reports it got 4 categories wrong; unclear reports go to a person instead of being guessed. We also wrote an LLM version to compare once we have an API key." |
| 2:20-3:20 | **Role 2: Forecast Lead** — Dikeledi | Forecast tab: the three numbers, chart, workload table, water in the category picker | "We compared four simple models on the last 12 weeks; the 4-week moving average was most accurate, off by about 4 reports a week. Expect 69 reports next week and 276 over the next month, level with recent weeks, so no surge alert. Water is the one category rising, about 8%." |
| 3:20-4:20 | **Role 3: Hotspot Lead** — Tshepo Tleane | Hotspots tab: click the rank 1 marker, show the ranked list | "We grouped reports by location with KMeans. Five clusters scored best on the silhouette check. Old Alexandra and East Bank produce 61% of reports, so that's where depots and crews should be. Tsutsumani is quietest, but quiet may mean under-reporting, which is next week's fairness check." |
| 4:20-5:00 | **Role 5: Dashboard Lead** | Back to headline numbers | "So: no surge expected this month, keep an eye on water, and put capacity in the two busiest areas. The limits are one year of synthetic data and simple models. Next we check fairness and test on real reports. Questions?" |

## If something goes wrong

- **Map is blank:** no internet for the map tiles. Show the ranked list and open `hotspots/hotspot_map.html` later, or describe the clusters from the table.
- **Dashboard shows "PLACEHOLDER":** `run_all.py` wasn't run. Run it (about 20 seconds) and refresh.
- **Running long:** cut the Data Lead's part to one sentence; the Forecast and Hotspot parts are the Week 5 focus.

## Likely questions

- *Why not a more advanced model?* With one year of data a complex model would overfit. The simple model is tested on past weeks and is off by about 4 reports a week.
- *Why 5 clusters?* The silhouette score was highest at 5, and the elbow chart flattens after 5 (`hotspots/cluster_count_check.png`).
- *How accurate is the classifier?* 26 of 30 tricky test reports were sorted correctly. It scores 100% on the dataset, but that is optimistic because the keywords were built from those reports.
- *Is this real data?* No, it's synthetic, so the findings show the method works, not what is happening in Alexandra.
