# Workflow

This folder holds the Week 7 report-to-team workflow. Each contributor owns one module:

- `pipeline.py`: accept a report, create a ticket, and load saved tickets.
- `approvals.py`: record supervisor approval, reassignment, or rejection.
- `notify.py`: save update emails as `.eml` files in `outbox/`.

## Shared ticket columns

Keep the CSV header and ticket dictionaries in this order:

`ticket_id, received_at, description_masked, ward, resident_contact, category, urgency, review_required, reason, assigned_team, depot, sla_hours, due_by, status, approval_status, approver, decision_note, last_updated`

The CSV lives at `workflow/data/tickets.csv`. The scaffold starts with the header only. Do not display `resident_contact` in the dashboard. The approved ward names are Old Alexandra, East Bank, Pan Africa, Far East Bank, Setswetla, and Tsutsumani. Teams are Water, Sanitation, Electricity, Roads, Waste, and Intake desk. Keep status labels consistent across the three modules and agree any new labels at the halfway check-in.

## Team checkpoints

- **Day 1:** create this folder, agree the ticket columns, and confirm an owner for each module.
- **Halfway check-in:** each owner shows one working path, names blockers, checks that the ticket fields still match, and agrees the next integration test.
- **Before each push:** run `git pull origin main`, then run the agreed tests.
- **Before committing:** each contributor checks their own Git author identity and commits from their own account. The Scrum Master should review commit authors in the shared history; this file cannot verify account ownership.

Run the project tests from the repository root with `python -m pytest forecast intake dashboard governance workflow`.

## The pipeline (Role 4)

`pipeline.py` runs every new report through the steps below and is what the Workflow tab and the command line call.

| Step | Function the pipeline calls | Owner | Until it exists |
| --- | --- | --- | --- |
| Route | `routing.route(ticket) -> ticket` (fills `assigned_team`, `depot`, `sla_hours`, `due_by`) | Role 1 | stand-in in `fallbacks.py` |
| Start approval | `approvals.start(ticket, now) -> ticket` (status `awaiting_approval` + approval `pending`, or `assigned` + `not_required`) | Role 2 | stand-in |
| Overdue | `approvals.escalate_overdue(tickets, now) -> changed tickets` | Role 2 | stand-in |
| Email | `notify.notify(event, ticket, resident_email=None, now=None)` for `received`, `assigned`, `approval_needed`, `overdue` | Role 3 | stand-in, saves to `outbox/` |

The pipeline uses a teammate's function as soon as it exists in the module, with no change to `pipeline.py`. The decision log names any stand-in still in use. When yours lands, delete the matching stand-in from `fallbacks.py` and its test from `test_fallbacks.py`.

**Saving decisions:** the Workflow tab calls `approvals.decide(...)` but doesn't save the ticket afterwards, so `decide` must save its result with `pipeline.save_ticket(ticket)`.

**Functions other code can use:** `process_report(text, ward, resident_email=None, now=None)`, `load_tickets()`, `save_ticket(ticket)`, `process_inbox(path)` and `check_overdue(now=None)`. The resident's email is only passed to the email step and is never saved.

**Commands:** `python workflow/pipeline.py --demo`, `--inbox <file.csv>` (columns `report_ref, description, ward, resident_email`; see `inbox/new_reports_example.csv`) and `--check-overdue`. Live files (`data/tickets.csv`, `data/processed_inbox.csv`, `inbox/`, `outbox/`) are not committed; `data/tickets_example.csv` shows the format.
