# Week 8 Industry Showcase Script

**Target:** 14 minutes, within the requested 12-15-minute presentation. These are rehearsal timings, not measured product results. Take panel questions after the presentation.

**Before starting:** Run `git pull origin main` before team work begins. Before every push, run it again and run the agreed tests. Do not push close to the showcase: a push rebuilds the live app and clears its demo tickets. See [workflow/README.md](../workflow/README.md) and [docs/deployment.md](deployment.md).

Use synthetic examples only. Rehearse the live path before presenting, and update the deck and this script together if any source figures change.

## Run of show

| Time | Presenter | Segment |
| --- | --- | --- |
| 0:00-1:15 | Andile Khoza, Role 5 | Resident story, team, purpose |
| 1:15-2:30 | petroblyn, Role 1 | What the system does and its limits |
| 2:30-7:00 | Dikeledi, Role 4 | Submit, route, approve, show email preview and decision log |
| 7:00-9:00 | Tshepo Tleane, Role 2 | Forecast and hotspot map |
| 9:00-10:00 | Thembelihle, Role 3 | Responsible AI |
| 10:00-10:50 | Tshepo Tleane, Role 2 | Business case |
| 10:50-11:45 | Andile Khoza, Role 5 | The ask |
| 11:45-12:45 | Dikeledi, Role 4 | Deployment and live-site limits |
| 12:45-13:15 | Thembelihle, Role 3 | Portfolio evidence and panel Q&A handover |
| 13:15-14:00 | Andile Khoza, Role 5 | Close |

## Spoken script and demo cues

### 0:00-1:15 | Andile: opening and introductions

**Say:** “Imagine a resident sees sewage flowing near homes where children play. They send a report and need it to reach the right team, with a person able to review it when the situation is urgent. This is a made-up example, not a real resident story.

“Hello, we are the Report Radar team: **Know where needs are rising.** I’m Andile Khoza, Showcase Lead and Scrum Master. With me are petroblyn, Tshepo Tleane, Thembelihle, and Dikeledi. We built a planning aid for municipal service reports in Alexandra, Johannesburg. Today we’ll follow a report through the workflow, then look at expected workload and where reports are concentrated. All project data is synthetic, so these results are not a claim about current service conditions.”

**Evidence:** [docs/one_page_explanation.md](one_page_explanation.md) describes the project and synthetic dataset; the sample report wording is in [workflow/inbox/new_reports_example.csv](../workflow/inbox/new_reports_example.csv).

### 1:15-2:30 | petroblyn: what Report Radar does

**Say:** “I’m petroblyn. Report Radar helps staff sort a report by problem and urgency, estimate incoming workload, and see where reports are concentrated. When the wording is unclear, the system can send it for a person to check. It supports planning; it does not repair the problem or replace a supervisor’s judgement. The forecast and map are estimates from synthetic reports and need checking before they guide real service decisions.”

**Handover:** “Dikeledi will show what happens to one report after it is submitted.”

**Evidence:** [docs/one_page_explanation.md](one_page_explanation.md) and [governance/model_cards/workflow.md](../governance/model_cards/workflow.md).

### 2:30-7:00 | Dikeledi: live report-to-approval demo

**Before the demo:** Confirm the live app is awake, the Workflow tab has its sections, and an approval test works. Use no resident email. If a freshly submitted report does not appear in the approval queue, do not claim that it did; use a clearly labelled prepared example or switch to the backup.

**Say and do:**

- “I’m Dikeledi. I’ll submit a synthetic report using wording from our sample inbox.” Open **Workflow**. Enter: “Sewage flowing into the Jukskei near homes where children play.” Choose **Setswetla** and leave the optional email blank. Select **Send report**.
- Note the ticket number shown after submitting. The live site already has an example ticket with identical wording, so use the ticket number, not the wording, to distinguish the new report.
- Point to the generated ticket reference, assigned team, and expected fix date. Say: “The date is an estimate, not a promise.” Do not read out an unverified value as a general service standard.
- In **My team’s queue**, choose the team shown on the ticket. Point to the report and its place in the queue. Say: “The queue puts higher-urgency work first, then the closest deadline.”
- In **Waiting for approval**, find and open the ticket with the number you noted after submitting. Do not approve the example ticket with the same wording. Read the selected ticket’s masked description before acting. Enter the presenter’s name and select **Approve**. Point out the confirmation. Say: “A person makes this decision; the system records it and notifies the team.”
- Open **Sent emails** and expand the update. Say: “This is a saved email preview for the demo. The site stores these messages; it does not send real email. Resident addresses are not displayed here.”
- Open **Risk & compliance** and scroll to **Latest decisions the system made**. Point to the new workflow entry and its reason. If the page says these are example decisions or the new entry is missing, say so and do not present the example as a live decision.

**Handover:** “You’ve seen the handoff and the human approval point. Tshepo will show how the wider report history can support planning.”

**Evidence:** [docs/week7_user_guide.md](week7_user_guide.md), [workflow/README.md](../workflow/README.md), [governance/model_cards/workflow.md](../governance/model_cards/workflow.md), and [docs/deployment.md](deployment.md). The email limitation is explicit in the deployment guide. The sample wording is in [workflow/inbox/new_reports_example.csv](../workflow/inbox/new_reports_example.csv).

### 7:00-9:00 | Tshepo Tleane: forecast and hotspot map

**Say and do:** “I’m Tshepo. In the Forecast tab, the current forecast is about **69 reports a week** for the next **four weeks**, or **276 in total**, with a likely range of **260-292**. It is broadly level with recent weeks, so this forecast does not signal a surge. These are estimates, not guaranteed counts.”

Open **Problem areas** and show the map. “The hotspot analysis covers **3,994 synthetic reports**. Old Alexandra and East Bank together account for **61%** of them. This shows where reports in this dataset are concentrated; it does not prove that other areas have fewer problems. We need to consider that some residents may report less often.”

**Handover:** “The results can help focus a conversation, but they also have limits. Thembelihle will cover how we handle those risks.”

**Evidence:** Forecast values: [forecast/insights.md](../forecast/insights.md). Map counts and share: [hotspots/insights.md](../hotspots/insights.md). The under-reporting caveat: [docs/week6_risk_report.md](week6_risk_report.md).

### 9:00-10:00 | Thembelihle: responsible AI

**Say:** “I’m Thembelihle. A report sorter can misunderstand language or miss context, so uncertain reports need a person’s review. Urgent work also has a supervisor approval point. The decision log records what the system decided and why, with personal details masked in the log. But there is an important limit: report text is still visible on the public dashboard. Our results use synthetic data only. Before real resident reports are used, that text must be masked on screen, residents need a way to see and correct their reports, and translations need fluent-speaker review.”

**Handover:** “With those safeguards in mind, Tshepo will make the business case and Andile will state our ask.”

**Evidence:** [docs/week6_risk_report.md](week6_risk_report.md), [governance/logger.py](../governance/logger.py), and [governance/model_cards/workflow.md](../governance/model_cards/workflow.md).

### 10:00-10:50 | Tshepo: business case

**Say:** “The practical opportunity is to bring the forecast and hotspot view into regular planning: check expected workload, discuss where reports are concentrated, and review urgent or unclear cases. The project recommends using the forecast in planning meetings and checking a surge alert when it appears. It also recommends validating the findings before operational decisions. Because our data is synthetic, we are not claiming savings, faster repairs, or proven demand in any area.”

**Evidence:** [docs/one_page_explanation.md](one_page_explanation.md) and [forecast/insights.md](../forecast/insights.md).

### 10:50-11:45 | Andile: the ask

**Say:** “Our ask is for an operational sponsor to help define a controlled next step: identify an authorized, representative sample for evaluation after the privacy safeguards are in place; invite service staff to review the routing and deadline rules; and agree what evidence would justify a limited pilot. Until that work is done, Report Radar remains a synthetic-data demonstration, not a tool for real resident decisions.”

**Evidence:** [docs/week6_risk_report.md](week6_risk_report.md) sets out the safeguards before real data is used; [docs/one_page_explanation.md](one_page_explanation.md) recommends testing on real reports before decisions are made.

### 11:45-12:45 | Dikeledi: deployment

**Say:** “The live dashboard is hosted on Streamlit Community Cloud and is built from the `main` branch. It is suitable for this showcase, but it is not a permanent case-management system: saved demo tickets and decisions can disappear when the app restarts or rebuilds. The email area is a preview, not a mail service. A real deployment would need persistent storage, controlled access, and an approved approach to contacting residents.”

**Evidence:** [docs/deployment.md](deployment.md) and [governance/model_cards/workflow.md](../governance/model_cards/workflow.md).

### 12:45-13:15 | Thembelihle: portfolio evidence

**Say:** “I’m responsible for the portfolio and panel Q&A material. We’ll use the portfolio to show the evidence behind the demo, what is complete, and what still needs validation. For question ownership, see [docs/week8_panel_qa.md](week8_panel_qa.md).”

**Note:** Role 3 should create `docs/week8_panel_qa.md` before the showcase so this link resolves.

### 13:15-14:00 | Andile: close

**Say:** “Report Radar turns synthetic service reports into a clearer view of workload, locations, and decisions that need a person. We have shown what it can do today and what must be checked before real use. With a municipal partner to guide a careful evaluation, we can test whether it is useful in practice. Thank you. We’re ready for your questions.”

## Panel question handover

Use [docs/week8_panel_qa.md](week8_panel_qa.md) for prepared answers. Route questions this way:

| Question area | First responder |
| --- | --- |
| Classification, technical documentation, system limits | petroblyn, Role 1 |
| Forecast, hotspots, business case and assumptions | Tshepo Tleane, Role 2 |
| Portfolio evidence, responsible AI, fairness and privacy | Thembelihle, Role 3 |
| Live site, workflow, approvals, emails and deployment | Dikeledi, Role 4 |
| Overall project, integration, delivery plan and the ask | Andile Khoza, Role 5 |

If a question crosses roles, the first responder gives the short answer and hands over to the owner of the evidence. Do not guess: offer to check the source document.

## Backup plan

### Screenshots

Capture one screenshot for each visible demo step, using synthetic data and no email address:

- Workflow form with the prepared report and area entered.
- Submission confirmation with ticket reference, team, and expected fix date.
- Team queue with the submitted report visible and sorted.
- Supervisor approval view with the masked report and decision controls.
- Approval confirmation.
- Sent email preview with recipient details hidden.
- Risk & compliance decision-log row, clearly showing whether it is live or an example.
- Forecast view with the current figures.
- Problem areas map and ranked areas.

Keep the screenshots available offline. Also record a **2-minute** screen capture of the same synthetic path, including the forecast and map, and keep the video available offline. Do not show actual resident information.

### If the live site or Wi-Fi fails

Say: “The live site or network is unavailable, so we’ll use our offline recording and screenshots of the same synthetic workflow. These show the demo path, not a live action right now.” Switch to the recording, then use screenshots for any detail that is hard to read. If the map cannot load because the connection is unavailable, show its screenshot. Do not say a report was submitted or approved live when it was not. If the backup does not show a step, explain that the step could not be demonstrated rather than inventing a result.

**Preflight:** Wake the live app **15 minutes** before the showcase and run the deployment guide’s **2-minute** post-push check well before presenting. Avoid a push in the **hour** before the showcase. See [docs/deployment.md](deployment.md).

## Rehearsal checklist

- Keep the run within the 14-minute target; each presenter practises their assigned time below.
- Andile: 2:55 total. petroblyn: 1:15. Tshepo: 2:50. Thembelihle: 1:30. Dikeledi: 5:30. These are rehearsal allocations from the run of show, not measured results.
- Rehearse each spoken handover; the next person should be ready on the correct tab before their segment starts.
- Explain “synthetic” as made-up project data; explain “hotspot” as an area with many reports. Avoid unexplained technical terms.
- Verify every number against the source ledger and make the deck match this script. If a source file changes, update both before presenting.
- Rehearse noting the submitted ticket number and approving that exact number in **Waiting for approval**, not the example ticket with the same wording.
- Confirm the workflow sample reaches supervisor approval, approval updates the ticket, an email preview appears, and the decision log identifies the new entry as live. If any check fails, use the labelled backup.
- Check that no email address or other personal information is visible in the live demo, screenshots, or recording.
- Ask each team member to answer one practice question about another role’s work.
- Before every push, run `git pull origin main` and the agreed tests. Do not push during the hour before the showcase.

## Number source ledger

Project figures are spoken with source notes above. The timing figures are rehearsal or task requirements, not product measurements.

| Number used | What it refers to | Source |
| --- | --- | --- |
| 12-15 minutes | Requested presentation length | Week 8 task brief; the 14-minute schedule above is the rehearsal plan |
| 14 minutes and presenter time allocations | Planned run of show | This script's **Run of show** and **Rehearsal checklist** |
| One minute | Responsible AI segment | Week 8 task brief and this script's run of show |
| 69 per week; four weeks; 276 total; likely range 260-292 | Workload forecast | [forecast/insights.md](../forecast/insights.md) |
| 3,994 reports; 61% | Synthetic hotspot dataset | [hotspots/insights.md](../hotspots/insights.md) |
| Two-minute recording | Requested backup duration; not a project performance figure | Week 8 task brief; [docs/deployment.md](deployment.md) requires an offline recording or screenshots but does not set the recording length |
| 15 minutes; two-minute check; one hour | App wake-up, post-push check, and no-push window | [docs/deployment.md](deployment.md) |

## Week 8 delivery log

- Showcase date: to be confirmed
- Showcase time: to be confirmed

### Halfway check-in

- Status: not held yet
- Date:
- Who attended:
- Blockers:

### Rehearsal log

| Date | Total time | What went wrong | What we changed |
| ---- | ---------- | --------------- | --------------- |
|      |            |                 |                 |
