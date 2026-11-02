# Workflow user guide

All example reports and tickets are synthetic. A ticket number is the reference to use when following up. The expected fix date is an estimate, not a guarantee.

## Residents

1. Open the **Workflow** tab.
2. Describe the problem and choose the area.
3. Add an email only if you want updates; it is optional and is only used to send updates.
4. Select **Send report**. Note the ticket number, assigned team, and expected fix date.

This is about four main interactions (open the tab, enter the problem, choose an area, submit), plus the optional email field. There is no email step if you leave it blank. This online form does not replace phone or in-person reporting for residents who cannot use it.

## Team members

1. Open **Workflow** and choose your team in **My team's queue**.
2. Read the queue from top to bottom: higher urgency comes first, then the closest deadline. Overdue tickets are called out.

This takes about two clicks: open the tab and choose a team. The queue uses friendly dates and does not show resident email addresses.

## Supervisors

1. Open **Workflow**, enter your name, and open a report under **Waiting for approval**.
2. Read the masked problem description and urgency before deciding.
3. Select **Approve**, **Reassign**, or **Reject**. Reassignment and rejection need a reason; reassignment also needs a team.
4. Check **Sent emails** to see whether an update was sent.

Approval takes about four interactions: open the tab, enter your name, open the report, and approve. Reassignment or rejection takes a few more to enter a team or reason and save. Do not approve a report before reading it.

## Outside-team form check

**Result: not yet run.** The report-processing module is still a scaffold, so the form cannot yet create a real ticket. No participant, duration, confusion, or change is claimed here.

After `workflow/pipeline.py` can submit a report, ask one person outside the team to complete the form using synthetic details. Start a timer when they open **Workflow** and stop when they can read their ticket number. Do not coach them. Record the actual elapsed time, the words or step that confused them, and the change made. Keep the participant anonymous; do not record a real resident email.

| Check | Result |
| --- | --- |
| Time to submit and find the ticket number | Pending the test |
| What confused the participant | Pending the test |
| Change made after watching the participant | Pending the test |
