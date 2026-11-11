# Portfolio entry: Dikeledi

## My roles by week
| Week | Role | What it was for |
|---|---|---|
| 5 | Forecast Lead, then integration | Forecast the weekly workload, then join the team's pieces into one working dashboard |
| 6 | Role 4: Logging and Transparency Lead | Record every decision the system makes, and explain each model in plain words |
| 7 | Role 4: Integration and Automation Lead | One command that takes a new report through every step, safely and on the record |
| 8 | Role 4: Deployment and Optimisation Lead | A live site that is ready to demo, and documented |

## What I built
**Week 5**
- **Workload forecast** (`forecast/forecast.py`). Weekly counts, three models compared by backtest, a 4-week forecast, per-category forecasts and plain-language insights with a surge alert. 14 tests in `forecast/test_forecast.py`. Commits: `662d11e`, `e60944d`, `14548db`.
- **Data generator, data check and rebuilt classifier** with 30 tricky test reports (`data/`, `intake/`). Commits: `94187b8`, `ce0fd65`.
- **One-command build and dashboard integration** (`run_all.py`, `dashboard/app.py`), then a plain-language pass for non-technical users. Commits: `c012f52`, `3dae793`.

**Week 6**
- **Decision log** (`governance/logger.py`). Every classifier, forecast and hotspot decision is logged with its reason and rules version; personal details are masked first; rows older than 12 months are deleted. 10 tests in `governance/test_logger.py`. Commits: `917d785`, `b99c61d`, `ed7064a`.
- **Model cards and transparency notes** (`governance/model_cards/`, `governance/transparency_notes.md`). Commits: `29f5aae`, `2efc785`.
- **Risk evaluation report** (`docs/week6_risk_report.md`). Commit: `3168e6c`.
- **Privacy fixes**: report text is masked before it goes to the LLM classifier, and more house-number, phone and ID formats are hidden. Commits: `744935e`, `ad05d9f`, `88c8c24`.

**Week 7**
- **Workflow pipeline** (`workflow/pipeline.py`). One function runs mask, classify, route, approve, email, save and log. A failed step still saves the ticket for a supervisor. It also processes an inbox file without duplicates and escalates overdue tickets. 19 tests in `workflow/test_pipeline.py`. Commits: `50d8b1e`, `cfb6be3`, `717f62d`.
- **Stand-ins for teammates' modules** (`workflow/fallbacks.py`), so the pipeline could be built and tested before routing, approvals and emails landed. Commit: `b567976`.
- **Integration fixes** found by clicking through the dashboard as a supervisor: decisions were not saved, Reassign always failed, and team names did not match between routing, the dashboard and the email list. Commits: `511dbc6`, `94240b7`, `d9fe16a`.
- **Workflow model card and 3 automation risks** (`governance/model_cards/workflow.md`, `governance/risk_register.csv`). Commit: `ef86260`.

**Week 8**
- **Live-site fixes**: a fresh copy loads 10 example tickets through the real workflow, and the Risk & compliance tab shows a labelled example decision log. Commits: `8cff177`, `09f5d85`.
- **Deployment guide** (`docs/deployment.md`). Commit: `cfa7405`.
- **Weekly summary for managers** (`dashboard/weekly_summary.py`), for all teams or one team, with a download. 8 tests in `dashboard/test_weekly_summary.py`. Commit: `c0f7e69`.
- **Business case slides** (`docs/week8_business_case.pdf`), built from Tshepo's outline with the team branding.

## Skills this shows
- **Python and data analysis:** pandas and scikit-learn in `forecast/forecast.py`; models chosen by backtest, not by guess.
- **Testing:** end-to-end tests that check no phone number, ID number or resident email reaches the tickets file, the outbox or the log (`workflow/test_pipeline.py`).
- **System integration:** joined five people's modules through one agreed ticket format (`workflow/README.md`) and fixed the faults between them.
- **Responsible AI:** decision logging, model cards and a risk report with ethical reasoning.
- **Deployment:** a Streamlit Community Cloud site with a written check to run after every push (`docs/deployment.md`).
- **Git teamwork:** small one-purpose commits on a shared `main` branch with 4 teammates.

## Tools I used
- Python, pandas, scikit-learn, Streamlit, pytest, Git and GitHub.
- Claude (AI assistant). It drafted code, tests and documents from my prompts, which are recorded in `docs/prompt_log.md`. I ran the build and the tests, checked the results against the dashboard and the live site, and pushed every change myself.

## What I learned
After my teammates' modules landed, every test passed but the dashboard was broken: no team saw its tickets and 7 of 8 team emails went to the supervisor, because routing used "Water team" and the dashboard used "Water". The mistake came from a prompt I had written. I learned that passing tests do not prove the parts fit together, so I now click through the whole flow as a user, and a test checks the team names agree.

I also learned that a site can work on my laptop and still look empty when deployed, because the live copy never runs the build step. I fixed it by loading labelled example tickets on a fresh copy.

## My 3-line CV summary
1. Built the forecasting, decision-logging and workflow-automation parts of a municipal service-report system in Python, with automated tests.
2. Integrated five people's modules into one tested pipeline and a live Streamlit dashboard, and fixed the faults found between them.
3. Wrote model cards, a risk report and a deployment guide in plain language for non-technical readers.

## Checked by
Teammate who checked this against the commit history: ______  Date: ______
