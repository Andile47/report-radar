# Portfolio entry: Thembelihle

## My roles by week
| Week | Role | What it was for |
|---|---|---|
| 5 | Dashboard work (role name to confirm) | Capacity planner and dashboard redesign |
| 6 | Role 3: Privacy and Data Governance Lead | Protect residents' personal details and record privacy risks |
| 7 | Role 3: Notifications Lead | Send update emails safely, without leaking personal details |
| 8 | Role 3: Portfolio and Panel Prep Lead | Prepare the portfolio template, panel questions and team contributions page |

## What I built
**Week 5**
- **Capacity planner** on the Forecast tab. A manager enters crews and reports per crew, and it answers: do we have enough crews? Commits: `28ac529`, `73de9e7`, merged in PR #1 (`107b8b2`).
- **Dashboard redesign**: navy and blue theme, Overview tab, KPI cards and filters. Commits: `000549d`, `fa37a2e`, merged in PR #2 (`982be3c`).

**Week 6**
- **Personal-information masking** (`governance/privacy.py`). It hides phone numbers, ID numbers, emails, house numbers and names before text is logged or sent. Tests: `governance/test_privacy.py`. Commit: `db456f2`, merged in PR #3 (`8c2b725`).
- **PII scan** (`governance/scan_pii.py`). It checked all 3,994 synthetic reports and found no personal details. Same commit.
- **Data card, POPIA checklist and 4 privacy risks** (`governance/data_card.md`, `governance/popia_checklist.md`, `governance/risk_register.csv`). Commits: `5e866ca`, `703b1e0`, merged in PR #4 (`7edccc1`).

**Week 7**
- **Email notifications** (`workflow/notify.py`). Four emails: received, assigned, approval needed and overdue. They are masked and saved as files. Real sending only happens if all three SMTP settings are set. A resident's address is never saved in the ticket, the outbox or the log. 13 tests in `workflow/test_notify.py`. Commit: `1c2b270`.
- **4 notification risks (R3-05 to R3-08) and a POPIA checklist update for emails.** Commits: `e286699`, `8056cfb`.

**Week 8**
- **Portfolio template** (`docs/portfolio/TEMPLATE.md`). Commit: `18e994a`.
- **Panel Q&A** with 22 questions, each with a source file and an owner (`docs/week8_panel_qa.md`). Commit: `15c426c`.
- **Team contributions page**, built from git history and the prompt log (`docs/team_contributions.md`). Commits: `79b8035`, `a6a5d27`.

## Skills this shows
- **Testing:** pytest tests for masking (`governance/test_privacy.py`) and notifications (`workflow/test_notify.py`).
- **Privacy and data protection:** masking, a PII scan, a data card and a POPIA checklist.
- **Python email handling:** `.eml` files and optional SMTP sending (`workflow/notify.py`).
- **Streamlit dashboards:** capacity planner and redesign.
- **Git teamwork:** pull requests, merging and working on `main` with 4 teammates.
- **Risk documentation:** 8 privacy and notification risks in `governance/risk_register.csv`.

## Tools I used
- Python, pytest, Streamlit, Git and GitHub.
- Claude (AI assistant). It helped me draft code, tests and documents. I ran every test, read every output and checked every claim against the repo before I committed.

## What I learned
My masking function used `[ID_NUMBER]`, but a teammate's logger test needed `[ID]`. The test failed, so I changed my function and all tests passed. I learned to agree on exact names with teammates before I write code that connects to theirs.

My first privacy check marked every email as a problem, because every email has a placeholder address. I made the check more specific and then found no real leaks. I learned that a check must test the right thing, or it gives a false alarm.

## My 3-line CV summary
1. Built privacy tools for a municipal service-report system: personal-information masking, a PII scan and a POPIA checklist.
2. Wrote automated tests and a safe email-notification module in Python that never stores or leaks a resident's address.
3. Worked in a team of five on GitHub, and wrote the risk register entries, panel Q&A and contributions record for a panel presentation.

## Checked by
Teammate who checked this against the commit history: Dikeledi  Date: 11 Nov 2026 (all 18 commit links exist; one mistyped link corrected)
