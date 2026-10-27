# Prompt log

A record of how AI tools were used on Report Radar, as asked for in the responsible-AI part of the rubric. **Each team member should add their own prompts below.** Only synthetic data was ever shared with an AI tool.

| Date | Who | Tool | What we asked | What we did with the answer |
| --- | --- | --- | --- | --- |
| 22 Oct 2026 | Dikeledi | Claude | Review the repo against the Week 1 brief and list what is missing, without implementing anything | Used the gap list to plan the work |
| 22 Oct 2026 | Dikeledi | Claude | Split the missing Week 5 work into roles so each person knows what to build | Shared as the team's role breakdown doc |
| 22 Oct 2026 | Dikeledi | Claude | Implement the Forecast Lead role, in 15 small commits | Reviewed and pushed `forecast/`: weekly counts, 3 models compared by backtest, 4-week forecast, per-category forecast, insights, tests |
| 22 Oct 2026 | Dikeledi | Claude | Check the forecast against the role guide (moving average plus trend, workload table, matplotlib chart, plain-English summary, limits) and add what is missing | Added the chart, workload table, combined moving-average-plus-trend model and the category driving the change |
| 23 Oct 2026 | Dikeledi | Claude | Check the whole project against the five-role guide and list what is missing | Found gaps in data, intake, dashboard and docs |
| 23 Oct 2026 | Dikeledi | Claude | Implement everything missing, one commit per role | Data generator, sample and checks; classifier rebuilt with tests and an LLM version; cluster-count check and map insights; dashboard integration, README, this log, one-pager and demo script |
| 27 Oct 2026 | Dikeledi | Claude | Week 6, Role 4 (Logging and Transparency Lead): build a decision log, connect it to the classifier and forecast without changing outputs, and write model cards, transparency notes and risk register rows | Checked that every output file is identical with logging on and off (fingerprint comparison), that personal details are masked in the log, and that all tests pass. Every figure in the model cards was checked against the real outputs. |

## What we checked ourselves

AI can sound confident and still be wrong, so these were checked by running the code, not by trusting the answer:

- **Forecast:** predictions sit within the range of recent weeks (61-78 a week) and are never negative; 14 tests pass.
- **Classifier:** the 30 tricky test reports were written *before* the keywords were tuned. Test-specific words the AI first added (e.g. a misspelling from the test set) were removed so the error count stays honest: 4 of 30 categories wrong.
- **Classifier bug found in review:** the typo fixer turned "whole" into "hole" and misfiled a streetlight report; fixed by only correcting words that keep their first letter.
- **Hotspots:** the AI's first insight text described East Bank as "in the west of Alexandra" and named the same area as both most urgent and quietest. Both were wrong or misleading and were rewritten; urgency differences of 3.0 to 3.1 are now reported as "similar everywhere".
- **Hotspot map:** it originally opened on central Johannesburg, about 10 km from the data; it is now centred on Alexandra.
- **Dashboard:** run in a browser and checked tab by tab.

## Prompts for teammates to add

- Data Lead: the prompt used to generate the original `data/reports.csv`.
- Hotspot Lead: the prompts used to write `hotspot_analysis.py`.
- Intake Lead: the prompts used for the first version of `classifier.py`.
- Dashboard Lead: the prompt used for the starter dashboard.
- Data Lead: the prompt used to build the capacity planner (`dashboard/capacity.py`): "My Streamlit dashboard reads forecast/projected_workload.csv and data/reports.csv. Write dashboard/capacity.py with a function plan(crews, per_crew, expected_per_week, unfixed_now) and a function show_capacity_planner() that asks a manager for crews and reports per crew and answers: do we have enough crews? Also write pytest tests for plan(). Explain each step like I am new to Python."
