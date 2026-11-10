# Report Radar

[![Open the live dashboard](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://reportradar.streamlit.app)

**Live dashboard:** [reportradar.streamlit.app](https://reportradar.streamlit.app). No install needed; it runs on the synthetic data in this repo. On a fresh visit it loads 10 example tickets so every tab has data; see [`docs/deployment.md`](docs/deployment.md) for how it is deployed, what resets, and the check to run after every push.

Report Radar helps a municipality see **when** citizen reports are likely to surge and **where** problems are concentrated. Citizens report issues such as burst pipes, potholes and load-shedding faults. Report Radar sorts each report by type and urgency, forecasts the next month's workload, and maps the hotspots, so teams can plan before the surge arrives.

**Week 5:** predictive insights (forecast and hotspots) on a dashboard.
**Week 6:** an AI risk and compliance layer: bias and fairness checks, privacy masking, a decision log, transparency notes and a risk report.

All data is synthetic: no real personal information is used.

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

`run_all.py` checks the data, classifies the reports, tests the classifier, builds the forecast, finds the hotspots and sends 10 example reports through the Week 7 workflow, in that order. The dashboard also runs without it, showing labelled placeholder data for any part that hasn't been built.

To run the tests: `python -m pytest forecast intake dashboard governance workflow`

## What the dashboard shows

The dashboard is written for readers without a technical background: it opens with a plain-language summary, every number says what it means, and technical detail sits in "More detail" sections.

- **Summary box:** a green box (or a red surge alert) saying how many reports to expect next week and next month, which problem type to keep an eye on, and which areas are busiest.
- **Headline numbers:** reports in the last year, urgent reports (high or danger to life), reports not fixed yet, and urgent reports not fixed yet. The urgency scale is explained underneath.
- **Weekly summary for managers (bottom of the Overview tab):** last week's reports for all teams or one team (department): totals against the week before, urgent and unfixed reports, time to fix, busiest areas, next week's forecast and the live workflow tickets. Preview it on the page or download it to share.
- **Workload forecast tab:** reports expected next week and over the next 4 weeks; a chart of the past year (blue) and the forecast (orange) with its likely range shaded; "What this means" in plain bullets; a week-by-week table; and a chart for one problem type, opening on the one that is rising.
- **Capacity planner (bottom of the Workload forecast tab):** enter the number of crews and how many reports one crew fixes in a week, and it says whether next month is covered, how far behind unfixed reports will fall if not, and how many crews you need.
- **Problem areas tab:** a bar chart and table ranking the areas from busiest to quietest, what that means, and an interactive map (the map needs an internet connection).
- **Reports tab:** opens on urgent reports that are not fixed yet, most urgent first, with plain column names. You can switch to reports that need checking by a person, or all reports, and show why the system chose each problem type and urgency.
- **Risk & compliance tab:** every risk the team found, highest first, with who it could harm and what we did; whether some areas wait longer; how well the classifier works in each language; the latest decisions the system made and why; and a button to download the risk evaluation report.
- **Workflow tab:** residents can submit a report and see its ticket number, assigned team, and expected fix date; team members can sort their open queue by urgency and deadline; supervisors can approve, reassign, or reject reports; sent update emails can be opened from the outbox. Resident email addresses are not shown elsewhere on the dashboard. Each section explains when its workflow file is not ready yet.
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

- [`docs/deployment.md`](docs/deployment.md): how the live dashboard is deployed and updated, what resets there, and the check before a demo
- [`docs/one_page_explanation.md`](docs/one_page_explanation.md): what Report Radar found, for non-technical readers
- [`docs/demo_script.md`](docs/demo_script.md): the 5-minute demo, who presents what
- [`docs/week7_user_guide.md`](docs/week7_user_guide.md): the Workflow steps for residents, team members, and supervisors
- [`docs/week7_demo_script.md`](docs/week7_demo_script.md): a five-minute report-to-approval walkthrough
- [`docs/prompt_log.md`](docs/prompt_log.md): the AI prompts used, for the responsible-AI part of the rubric
- [`docs/week6_risk_report.md`](docs/week6_risk_report.md): the Week 6 risk evaluation report, with our ethical reasoning
- [`docs/week6_demo_script.md`](docs/week6_demo_script.md): the Week 6 demo, who presents which risk, and the ethics discussion

## Week 8 deliverables

- [Brand guide](docs/brand.md)
- [Technical documentation](docs/technical_documentation.md) (Role 1: petroblyn)
- [Deployment guide](docs/deployment.md) (Role 4: Dikeledi)
- [Business case deck](docs/week8_business_case.pdf) (Role 2: Tshepo Tleane)
- [Portfolios](docs/portfolio/) (Role 3: Thembelihle)
- [Panel Q&A](docs/week8_panel_qa.md) (Role 3: Thembelihle)
- [Presentation script](docs/week8_presentation_script.md) (Role 5: Andile Khoza)

## Governance (Week 6)

The `governance/` folder holds the risk and compliance work:

| What | Files | Owner |
| --- | --- | --- |
| **Classifier bias:** the same problems in six South African languages plus vulnerable residents, accuracy before and after | `bias_test_reports.csv`, `bias_check.py`, `bias_results_*.csv`, `classifier_bias.md` | Role 1: petroblyn |
| **Area fairness:** waiting times by area, a 1.5× fairness rule, the hotspot feedback loop | `area_fairness.py`, `area_fairness.csv`, `area_fairness.png`, `area_fairness.md` | Role 2: Tshepo Tleane |
| **Privacy (POPIA):** masking of names, phone, ID and house numbers and emails; data card; POPIA checklist | `privacy.py`, `scan_pii.py`, `data_card.md`, `popia_checklist.md` | Role 3: Thembelihle |
| **Decision log and transparency:** every sorted report, forecast and hotspot run recorded with its reason; model cards; "How this was decided" notes | `logger.py`, `logs/`, `model_cards/`, `transparency_notes.md` | Role 4: Dikeledi |
| **Risk register and report:** every risk scored and assigned; the Risk & compliance tab | `risk_register.csv`, `dashboard/risk_tab.py`, `docs/week6_risk_report.md` | Role 5: Andile Khoza |

All files are in `governance/` unless a folder is shown.

- **Decision log:** created when you run `python run_all.py` and not committed; `governance/logs/decisions_example.csv` shows the format. Personal details are masked before writing, and rows older than 365 days are deleted automatically. To switch logging off, set `REPORT_RADAR_LOGGING=off`; to change how long rows are kept, set `REPORT_RADAR_LOG_RETENTION_DAYS`.
- **Risk register:** everyone adds rows at the end of `governance/risk_register.csv` in the same format; `pytest governance` checks it (unique IDs, ratings 1-5, score = likelihood × impact).
- **Before any real resident data is used:** mask report text on the dashboard, add a login, give residents a way to see and correct their reports, and have fluent speakers check every translated phrase. See the risk report's next steps.

## Workflow (Week 7)

The `workflow/` folder contains the agreed ticket columns and the report, approval, and email module handoffs. Tickets are saved in `workflow/data/tickets.csv`; sent messages are saved as `.eml` files in `workflow/outbox/`. The `workflow/README.md` records the team checkpoints and commit-identity checklist. Run all tests with `python -m pytest forecast intake dashboard governance workflow`.

Every new report runs through one automated pipeline (`workflow/pipeline.py`): mask personal details, classify, route to a team with a deadline, wait for a supervisor if urgent or unclear, save the ticket, email the right people, and log the decision. If a step fails, the ticket is still saved to the supervisor's approval queue. Commands:

```bash
python workflow/pipeline.py --demo            # 10 example reports (safe to repeat)
python workflow/pipeline.py --inbox new.csv   # process new reports; never creates duplicates
python workflow/pipeline.py --check-overdue   # escalate tickets past their deadline
```

Live tickets, the inbox and sent emails stay on each computer and are not committed. See `workflow/README.md` for how teammates' modules plug in, and `governance/model_cards/workflow.md` for what is automated and what still needs a person.

## Optional: the LLM classifier

`intake/llm_classifier.py` can classify reports with Claude instead of keywords. It needs `pip install anthropic` and an `ANTHROPIC_API_KEY`. Without them, everything else still works and the keyword classifier is used. Personal details are masked before any text is sent, and nothing is sent if the masking module is missing.
