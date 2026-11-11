# Portfolio entry: Tshepo Tleane

> Draft started on 11 Nov 2026 from the git history and `docs/prompt_log.md`. **Tshepo: check every line, then fill in the sections marked "to complete" in your own words.**

## My roles by week
| Week | Role | What it was for |
|---|---|---|
| 5 | To complete (role name) | Find and map where reports are concentrated |
| 6 | Role 2: area fairness | Check whether some wards wait longer than others |
| 7 | Role 2: Approval Workflow Lead | Decide which tickets need a supervisor, and escalate overdue ones |
| 8 | Role 2: Business Case Lead | Make the case to a municipal executive |

## What I built
**Week 5**
- **Hotspot analysis** (`hotspots/hotspot_analysis.py`). Validates coordinates, clusters reports with reproducible KMeans, ranks the clusters and draws an interactive map. Commits: `c2be46d`, `a50094c`, `88b4401`, `ff55d8a`, `28933d7`.

**Week 6**
- **Area fairness analysis** (`governance/area_fairness.py`, `governance/area_fairness.md`). Ward metrics, an urgent-wait chart, tests and written findings: urgent reports took a median of 44.3 hours in Tsutsumani against 23.55 in Old Alexandra (synthetic data). Commits: `9d2e16d`, `a6d1b9b`, `a36e786`, `bf7650b`, `3409c9d`.
- **3 fairness risks** in the risk register. Commits: `50f81bd`, `b41b122`, `918561b`.

**Week 7**
- **Approval workflow** (`workflow/approvals.py`). Allowed status moves, which tickets need a supervisor, approve, reassign and reject decisions, and overdue escalation, with tests and 2 risks. Commits: `472c4f6`, `07e12bd`, `ecfea97`, `c1a6a6e`.

**Week 8**
- **Business case outline** (`docs/week8_business_case_outline.md`). 11 slides and a backup slide, each with a headline, visual, speaker notes and sources. Commits: `11d1f47` to `e966420`. Dikeledi built the slides from it (`docs/week8_business_case.pdf`).

## Skills this shows
To complete: name each skill and the file that proves it. Starting points from your commits:
- Clustering and mapping (`hotspots/hotspot_analysis.py`)
- Fairness analysis (`governance/area_fairness.py`)
- State-machine design and testing (`workflow/approvals.py`, `workflow/test_approvals.py`)
- Business communication (`docs/week8_business_case_outline.md`)

## Tools I used
- Python, Git and GitHub, pandas, scikit-learn, Folium, pytest.
- GitHub Copilot (Weeks 7 and 8, recorded in `docs/prompt_log.md`). To complete: say what it helped with, and what you checked or changed yourself. Add any tools you used in Weeks 5 and 6.

## What I learned
To complete: two or three honest sentences. Include one thing that went wrong and how you fixed it.

## My 3-line CV summary
To complete:
1.
2.
3.

## Checked by
Teammate who checked this against the commit history: ______  Date: ______
