# Portfolio entry: petroblyn

> Draft started on 11 Nov 2026 from the git history and `docs/prompt_log.md`. **petroblyn: check every line, then fill in the sections marked "to complete" in your own words.**

## My roles by week
| Week | Role | What it was for |
|---|---|---|
| 5 | To complete (role name) | First ticket classification and urgency scoring |
| 6 | Role 1: classifier bias | Check whether the report sorter treats languages and wording fairly |
| 7 | Role 1: Routing Lead | Decide which team gets each ticket, from which depot, and by when |
| 8 | Role 1: Technical Documentation Lead | One document that explains the whole system |

## What I built
**Week 5**
- **First ticket classification and urgency scoring**, and CSV validation and reporting. Commits: `0550d52`, `66f20c1`.

**Week 6**
- **Multilingual bias tests and a metrics runner** (`governance/bias_test_reports.csv`, `governance/bias_check.py`), with results saved before and after the fix. Commits: `2f55d96`, `623eb16`, `33a2301`, `9db519d`.
- **Multilingual keywords for all six problem types** and translated urgency phrases in the classifier. Commits: `99e5cc8` to `9b71043`, `8a56a44`, `0d971a9`.
- **Accessibility and Unicode matching**, with a wheelchair-safety escalation test. Commits: `02d9be5`, `c50a6da`.
- **Bias findings and language-coverage risks** (`governance/classifier_bias.md`, `governance/risk_register.csv`). Commits: `392fe43`, `076e593`.

**Week 7**
- **Ticket routing** (`workflow/routing.py`, `workflow/routing_rules.csv`, `workflow/depots.csv`). Team by problem type, depot by ward, and a deadline that depends only on urgency, never on the ward. Every decision is logged. Commits: `9580015`, `9bc93f6`, `1140382`, `3e2f384`.
- **Routing tests** (`workflow/test_routing.py`) for every category, unknown values, deadlines and ward fairness. Commits: `2f1a92d`, `e6a2f8b`, `609851b`, `e2660b2`.
- **2 routing risks** in the risk register. Commits: `449c845`, `35a2323`.

**Week 8**
- **Technical documentation** (`docs/technical_documentation.md`), with an architecture diagram, and its README link. Commits: `a2087d7`, `90f2810`.

## Skills this shows
To complete: name each skill and the file that proves it. Starting points from your commits:
- Bias testing across languages (`governance/bias_check.py`)
- Rule design with a fairness constraint (`workflow/routing.py`)
- Testing (`workflow/test_routing.py`)
- Technical writing (`docs/technical_documentation.md`)

## Tools I used
- Python, Git and GitHub, pytest.
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
