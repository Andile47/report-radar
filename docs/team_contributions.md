# Team contributions, Weeks 5 to 8

Who did what, built from the git history (`git log --format="%ae|%ad|%s" --date=short`) and `docs/prompt_log.md`. Where neither source shows a contribution, the cell is left blank for that person to fill in. Nothing here is guessed.

**Names in git.** People committed under more than one name. Matched by email and confirmed by the team:
- Dikeledi = "Dikeledi" and "Dikeledi Kwenaite"
- petroblyn = "Petro Blyn" and "petroblyn"
- Andile Khoza = "Andile47" and "Andile Khoza"
- Tshepo Tleane = "Tshepo Tleane"
- Thembelihle = "Lihle15" and "Lihle Molope"

**How to read this.** Commit counts don't measure contribution, so none are shown. Where one person improved another's file, it is listed as "edited [name]'s file". Commits on 2 Nov belong to both Week 6 and Week 7, and were sorted by their messages. Each person should check their own rows and fill in the blanks.

## Week 5 (22 to 26 Oct): building the first version
| Person | Role | What git shows | Prompt log |
|---|---|---|---|
| Dikeledi | | Forecast module (weekly counts, 3 models compared by backtest, 4-week forecast, per-category forecast, insights, tests, chart); data generator, sample and data check; rebuilt classifier with weighted keywords, LLM version and 30 tricky test reports; cluster-count check and map centred on Alexandra; dashboard integration, `run_all.py`, plain-language dashboard | 22 and 23 Oct rows |
| petroblyn | | Ticket classification and urgency scoring; CSV validation and reporting (22 Oct) | |
| Tshepo Tleane | | Hotspot analysis module: coordinate validation, KMeans clustering, ranking, hotspot map (23 Oct) | |
| Andile Khoza | | Repository set-up, README, dashboard starter (22 Oct) | |
| Thembelihle | | Capacity planner on the Forecast tab (PR #1, 24 Oct); navy and blue theme and dashboard redesign with Overview tab, KPI cards and filters (PR #2, 26 Oct) | |

Note: the prompt log says Dikeledi implemented the missing Data, Intake and Dashboard pieces on 23 Oct ("Implement everything missing, one commit per role"). Each person should say in their portfolio entry which Week 5 parts were theirs.

## Week 6 (27 Oct to 2 Nov): risk and governance
| Person | Role | What git shows | Prompt log |
|---|---|---|---|
| petroblyn | Role 1 | Multilingual bias tests and metrics, multilingual keywords for six categories, translated urgency phrases, Unicode matching, wheelchair escalation test, bias findings, language risks (30 Oct) | |
| Tshepo Tleane | Role 2 | Area fairness analysis, ward fairness metrics, urgent-wait chart, tests, findings, three fairness risks (30 Oct) | |
| Thembelihle | Role 3, Privacy and Data Governance Lead | `mask_personal_info()`, tests and PII scan (PR #3); data card, privacy risks, POPIA checklist, prompt log entries (PR #4) (2 Nov) | 2 Nov, 3 rows |
| Dikeledi | Role 4, Logging and Transparency Lead | Decision logger with masking, logging of classifier, forecast and hotspot runs, 12-month log deletion, model cards, transparency notes, risk evaluation report, demo script (27 Oct and 2 Nov). Edited Thembelihle's `privacy.py` (house-number masking) and `test_capacity.py` | 27 Oct and 2 Nov rows |
| Andile Khoza | Role 5 | Governance folder and risk register template, Risk & compliance tab, downloadable risk report, tests for the report builder (27 and 30 Oct) | |

## Week 7 (2 to 6 Nov): workflow automation
| Person | Role | What git shows | Prompt log |
|---|---|---|---|
| petroblyn | Role 1, Routing Lead | `workflow/routing.py`: team and depot rules, urgency-based deadlines, logging and versioning, tests, two risks (6 Nov) | 6 Nov row (Copilot) |
| Tshepo Tleane | Role 2, Approval Workflow Lead | `workflow/approvals.py`: status transitions, tests, rules version, approval risks (2 Nov) | 2 Nov row (Copilot) |
| Thembelihle | Role 3, Notifications Lead | `workflow/notify.py` (four emails, masked, saved to outbox, optional SMTP), 13 tests, notification risks R3-05 to R3-08, POPIA checklist update (6 Nov). Updated one line in Dikeledi's `workflow/test_pipeline.py` to match | 6 Nov, 2 rows |
| Dikeledi | Role 4, Integration and Automation Lead | Ticket store, pipeline (mask, classify, route, approve, email, save, log), inbox command, overdue escalation, workflow demo, model card, integration fixes (decisions saved through the pipeline, working Approve/Reassign/Reject, agreed team names) (2 and 6 Nov). Edited Thembelihle's `privacy.py` (bracketed phone and ID formats). Added translation review sheet and script | 2 and 6 Nov rows |
| Andile Khoza | Role 5, User Experience Lead and Scrum Master | Workflow dashboard tab (2 Nov). Week 7 user guide and demo script: | 2 Nov row (Copilot) |

## Week 8 (10 Nov onwards): showcase (in progress)
| Person | Role | What git shows | Prompt log |
|---|---|---|---|
| petroblyn | Role 1, Technical Documentation Lead | `docs/technical_documentation.md` and its README link | |
| Tshepo Tleane | Role 2, Business Case Lead | Slide deck: | |
| Thembelihle | Role 3, Portfolio and Panel Prep Lead | Portfolio template and panel Q&A. Still to come: this page, own portfolio entry, checking the team's entries | |
| Dikeledi | Role 4, Deployment and Optimisation Lead | Example tickets and decision log load on a fresh copy, deployment guide, downloadable weekly summary | 10 Nov, 2 rows |
| Andile Khoza | Role 5, Showcase Lead and Scrum Master | Brand guide, presentation script, README index of deliverables, backup checklist, delivery log, demo screenshots | 10 Nov, 2 rows (Copilot) |

## Still to fill in
Blank cells above, and any Week 5 roles, are for each person to complete in their own portfolio entry (`docs/portfolio/<name>.md`) with a file or commit to point to.
