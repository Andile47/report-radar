# Report Radar: Week 7 workflow demo

**Length:** 5 minutes. Use synthetic details only. Before presenting, finish the workflow modules, run `python -m pytest forecast intake dashboard governance workflow`, and start the dashboard with `streamlit run dashboard/app.py`.

| Time | Presenter | Show | Say |
| --- | --- | --- | --- |
| 0:00-0:25 | Role 5, UX lead | Workflow tab | "This demo follows one synthetic report from a resident to a service team and a supervisor. Resident email addresses are not shown in the dashboard." |
| 0:25-1:20 | Resident | Report a problem | Enter a short synthetic water problem, choose Old Alexandra, leave email blank, and submit. Point out the ticket number, assigned team, and expected fix date. |
| 1:20-2:10 | Team member | My team's queue | Choose the assigned team. Point out that higher urgency appears first, the closest deadline breaks ties, and overdue tickets are highlighted. |
| 2:10-3:35 | Supervisor | Waiting for approval | Open the same ticket, read its masked description and urgency, enter the approver name, then approve it. Mention that reassignment and rejection require a reason. |
| 3:35-4:25 | Supervisor | Sent emails | Open the latest message and point out its subject, recipient label, time, and update text. Do not reveal an email address. |
| 4:25-5:00 | Role 5, UX lead | Workflow tab | Recap the handoff: the resident received a reference, the team saw its work, and the supervisor recorded a decision. State any sections that are still unavailable. |

## If a section is not ready

The dashboard should show a friendly message for a missing workflow module, ticket file, or outbox. Do not present an unavailable action as completed. If the report has not produced a ticket, stop the live handoff and describe the remaining step instead of inventing a ticket or email.
