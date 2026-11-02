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
