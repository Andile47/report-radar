# Model card: Workflow automation (report to team)

*Report Radar · Week 7 · last reviewed 2 Nov 2026 · rules version `workflow-2026.11`*

## What it is for

It takes a new citizen report all the way from "a resident typed something" to "a team has it, with a deadline, and the right people have been emailed", without anyone copying data by hand. Urgent or unclear reports wait for a supervisor first.

**Don't use it for:** closing or rejecting reports without a person, deciding a team's performance, or contacting residents for anything other than updates on their own report.

## How it works, in plain words

One function, `process_report()` in `workflow/pipeline.py`, runs these steps in order for every new report:

| Step | What happens | Who owns it |
| --- | --- | --- |
| 1. Mask | Names, phone and ID numbers, emails and house numbers are hidden | Role 3 (`governance/privacy.py`) |
| 2. Classify | Problem type and urgency from 1 to 5 | Intake (`intake/classifier.py`) |
| 3. Route | Team, depot and deadline; the deadline depends only on urgency, never on the area | Role 1 (`workflow/routing.py`) |
| 4. Approve | Urgent (4-5) or unclear reports wait for a supervisor; the rest go straight to the team | Role 2 (`workflow/approvals.py`) |
| 5. Save | One row in `workflow/data/tickets.csv`, in the team's agreed columns | Role 4 |
| 6. Email | Resident (if they gave an email), team or supervisor; saved to the outbox, not really sent | Role 3 (`workflow/notify.py`) |
| 7. Log | One row in the decision log: what was decided, why, and which rules version | Role 4 (`governance/logger.py`) |

Until a teammate's module is ready, a clearly marked stand-in in `workflow/fallbacks.py` does that step, and the decision log says which stand-ins were used.

**Automation:**

- `python workflow/pipeline.py --inbox <file.csv>` processes every new report in a file. It remembers what it has done, so running it again (for example every 15 minutes) never creates duplicate tickets.
- `--check-overdue` escalates tickets past their deadline and emails the supervisor.
- `--demo` sends 10 made-up reports through; it is step 6 of `python run_all.py`.

## What is automated, and what still needs a person

| Automated | Needs a person |
| --- | --- |
| Masking, sorting, routing, deadlines | Approving, reassigning or rejecting urgent and unclear reports |
| Saving tickets and logging every decision | Checking reports the system couldn't sort (Intake desk) |
| Emails to residents, teams and supervisors | Fixing the problem and marking it resolved |
| Escalating overdue tickets | Deciding what to do about an escalated ticket |

## How reliable it is

- **Tested end to end:** 19 workflow tests cover urgent and minor reports, failed steps, overdue escalation, repeat runs and privacy. They check that no phone number, ID number, name or resident email reaches the tickets file, the outbox or the decision log.
- **It never silently loses a report.** If any step fails, the ticket is still saved, sent to the supervisor's approval queue with a note naming the failed step, and the supervisor is emailed.
- **The demo** (10 example reports) put 4 of 10 in the approval queue: 3 urgent and 1 unclear.

## Known limits and risks

- **It's only as good as each step.** A wrong urgency from the classifier sends a report to the wrong queue with the wrong deadline (see the classifier model card: 4 of 30 tricky reports sorted wrong).
- **Stand-ins are in use** for routing, approvals and emails until teammates' modules land. They follow the agreed rules but are simpler than the final versions.
- **Deadlines are assumptions** (24 hours for urgency 5 up to 14 days for urgency 1), not real crew capacity.
- **Automation can hide problems.** A step that quietly produces poor results, rather than failing, won't be flagged. Check the decision log and the Intake desk queue regularly.
- **No real emails yet.** Messages are saved to `workflow/outbox/`; sending needs a mail server and a decision on consent.
- **Synthetic data.** It hasn't been tested on real reports or with real teams.

## Who to contact

Integration and Automation Lead: Dikeledi. Code: `workflow/pipeline.py`, `workflow/fallbacks.py`. Details: `workflow/README.md`.
