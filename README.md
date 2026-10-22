# Report Radar

Citizens report problems (potholes, water outages, load-shedding faults). Our system classifies each report, scores urgency, and predicts **when** reports will surge and **where** the hotspots are.

**Week 5 focus:** predictive insights (forecast + hotspots) shown on a dashboard.

## Team

| Role | Name | Folder |
|---|---|---|
| Data Lead | TODO | `/data` |
| Forecast Lead | TODO | `/forecast` |
| Hotspot Lead | TODO | `/hotspots` |
| Intake and Urgency Lead | TODO | `/classifier` |
| Dashboard, Integration and Docs Lead | TODO | `/dashboard`, `/docs` |

## How to run

```bash
git clone <repo-url>
cd report-radar
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run dashboard/app.py
```

The dashboard shows placeholder data for any file that is missing, so it always runs.

## Data contract

`data/reports.csv`
`report_id, timestamp, category, description, ward_or_suburb, latitude, longitude, urgency, status, hours_to_resolve`

`forecast/output.csv`
`week_start, actual, forecast`

`hotspots/clusters.csv`
`cluster, area_name, report_count, latitude, longitude`

## What each part does

- **Data:** synthetic reports with seasonal patterns, surge periods and uneven reporting between wards. TODO
- **Forecast:** TODO (method, what it predicts, limits)
- **Hotspots:** TODO (method, number of clusters, what the map shows)
- **Classifier:** TODO (keywords vs LLM, test results)
- **Dashboard:** Streamlit app combining all of the above.

## Limits and honest notes

- All data is synthetic. No real personal data is used.
- TODO: model limits, what we would do with more time.

## AI use log

| Who | Tool | What we asked it to do | What we changed or checked |
|---|---|---|---|
| TODO | TODO | TODO | TODO |
