# Report Radar

Report Radar helps a municipality see **when** citizen reports are likely to surge and **where** problems are concentrated. Citizens report issues such as burst pipes, potholes and load-shedding faults. Report Radar sorts each report by type and urgency, forecasts the next month's workload, and maps the hotspots, so teams can plan before the surge arrives.

**Week 5 focus:** predictive insights (forecast and hotspots) on a dashboard. All data is synthetic: no real personal information is used.

## How to run

You need Python 3.10 or newer.

```bash
git clone https://github.com/Andile47/report-radar.git
cd report-radar
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run_all.py                 # builds every output, about 20 seconds
streamlit run dashboard/app.py    # opens the dashboard in your browser
```

`run_all.py` checks the data, classifies the reports, tests the classifier, builds the forecast and finds the hotspots, in that order. The dashboard also runs without it, showing labelled placeholder data for any part that hasn't been built.

To run the tests: `pytest forecast intake`

## What the dashboard shows

The dashboard is written for readers without a technical background: it opens with a plain-language summary, every number says what it means, and technical detail sits in "More detail" sections.

- **Summary box:** a green box (or a red surge alert) saying how many reports to expect next week and next month, which problem type to keep an eye on, and which areas are busiest.
- **Headline numbers:** reports in the last year, urgent reports (high or danger to life), reports not fixed yet, and urgent reports not fixed yet. The urgency scale is explained underneath.
- **Workload forecast tab:** reports expected next week and over the next 4 weeks; a chart of the past year (blue) and the forecast (orange) with its likely range shaded; "What this means" in plain bullets; a week-by-week table; and a chart for one problem type, opening on the one that is rising.
- **Capacity planner (bottom of the Workload forecast tab):** enter the number of crews and how many reports one crew fixes in a week, and it says whether next month is covered, how far behind unfixed reports will fall if not, and how many crews you need.
- **Problem areas tab:** a bar chart and table ranking the areas from busiest to quietest, what that means, and an interactive map (the map needs an internet connection).
- **Reports tab:** opens on urgent reports that are not fixed yet, most urgent first, with plain column names. You can switch to reports that need checking by a person, or all reports, and show why the system chose each problem type and urgency.
- **Filters (left):** type of problem, area, minimum urgency and a search of what residents wrote. They change the headline numbers and the Reports tab; the forecast and problem areas always use every report.
- **How to read this page:** each tab has a short guide that opens with one click.

## How it fits together

```
data/reports.csv ──► intake/classifier.py ──► category, urgency, review flag ──┐
        │                                                                      │
        ├──────────► forecast/forecast.py ───► weekly forecast + workload ─────┼──► dashboard/app.py
        │                                                                      │
        └──────────► hotspots/hotspot_analysis.py ► clusters + map ────────────┘
```

## Team

| Role | Name | Folder | Hands over |
| --- | --- | --- | --- |
| 1. Data Lead | Thembelihle | `data/` | `reports.csv`, 20-row sample, generator script, data check |
| 2. Forecast Lead | Dikeledi | `forecast/` | 4-week workload table, forecast chart, insight sentences |
| 3. Hotspot Lead | Tshepo Tleane | `hotspots/` | Hotspot map, ranked areas, insight sentences |
| 4. Intake and Urgency Lead | petroblyn | `intake/` | Classifier, LLM version, 30-report test result |
| 5. Dashboard, Integration and Docs Lead | Andile Khoza | `dashboard/`, `docs/` | Dashboard, README, one-page explanation, demo script |

Each folder has its own README explaining how that part works, its results and its limitations.

## Data contract

The agreed columns, used by every module:

`report_id, timestamp, category, description, ward_or_suburb, latitude, longitude, urgency (1-5), status, hours_to_resolve`

**Categories:** `water`, `electricity`, `roads`, `sanitation`, `refuse`, `streetlights`. These replaced the first agreed list (water, roads, electricity, waste) because sewage and street-lighting faults are common reports. See `data/README.md` for the full data dictionary.

| File | Made by | Columns |
| --- | --- | --- |
| `data/reports.csv` | Data Lead | the agreed columns above |
| `intake/data/reports_classified.csv` | Intake Lead | agreed columns + `predicted_category, predicted_urgency, review_required, reason` |
| `forecast/output.csv` | Forecast Lead | `week_start, actual, forecast` |
| `forecast/projected_workload.csv` | Forecast Lead | `week_start, expected_reports, likely_low, likely_high` |
| `hotspots/clusters.csv` | Hotspot Lead | `rank, area_name, report_count, latitude, longitude`, plus centre, main problem and average urgency |

## Documents

- [`docs/one_page_explanation.md`](docs/one_page_explanation.md): what Report Radar found, for non-technical readers
- [`docs/demo_script.md`](docs/demo_script.md): the 5-minute demo, who presents what
- [`docs/prompt_log.md`](docs/prompt_log.md): the AI prompts used, for the responsible-AI part of the rubric

## Optional: the LLM classifier

`intake/llm_classifier.py` can classify reports with Claude instead of keywords. It needs `pip install anthropic` and an `ANTHROPIC_API_KEY`. Without them, everything else still works and the keyword classifier is used.
