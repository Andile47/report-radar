# Report Radar: panel questions and answers

Prepared answers for the Week 8 panel. All project figures come from synthetic (made-up but realistic) data for Alexandra, Johannesburg, so none of them is a claim about real service conditions. If a question is outside what a file tells us, say "We haven't tested this yet" and offer to check the source.

First responders follow the handover table in [week8_presentation_script.md](week8_presentation_script.md): petroblyn (classification, technical limits), Tshepo (forecast, hotspots, business case), Thembelihle (responsible AI, fairness, privacy), Dikeledi (live site, workflow, deployment), Andile (overall project, the ask).

## Business value

**1. What problem does Report Radar solve?** (Tshepo)
Every resident report has to be read, sorted, prioritised and sent to the right team. When reports surge, teams fall behind and urgent problems wait. Report Radar sorts reports by problem and urgency, forecasts the next 4 weeks of workload and maps where reports are concentrated. It supports planning; it does not fix problems or replace a supervisor.
Source: docs/one_page_explanation.md

**2. How much money or time will it save?** (Tshepo)
We haven't tested this yet. The data is synthetic, so we are not claiming savings, faster repairs or proven demand. To find out, we would run it on an authorised sample of real reports and compare it with how reports are handled today.
Source: docs/week8_presentation_script.md (business case section), docs/one_page_explanation.md

**3. Can a manager get a weekly report?** (Dikeledi)
Yes. At the bottom of the Overview tab, a weekly summary shows last week's reports for all teams or one team: totals against the week before, urgent and unfixed reports, time to fix, busiest areas, next week's forecast and the live workflow tickets. It can be previewed on the page or downloaded.
Source: README.md (weekly summary entry), dashboard/weekly_summary.py

**4. Can it reply to residents automatically?** (Dikeledi)
Only in a limited way. It writes a fixed update for the resident (ticket number, team, expected fix date) if they give an email address, and similar notes for the team and supervisor. On the live site these are saved previews. It does not send real email and does not write custom replies. Real sending would need mail settings and an approved approach to contacting residents.
Source: docs/deployment.md, governance/model_cards/workflow.md, workflow/notify.py

## Accuracy and limits

**5. How accurate is the report sorter?** (petroblyn)
On 30 deliberately tricky test reports it chose the right category 26 times. The mistakes came from unusual wording, for example "dead dog on the pavement" was not recognised as a refuse problem. This was a small tricky test, not a sample of real reports, and we haven't tested accuracy on real reports yet. When it is unsure it marks the report for a person to check instead of guessing.
Source: docs/one_page_explanation.md

**6. How accurate is the forecast?** (Tshepo)
Tested on past weeks, it is usually within about 4 reports a week of what happened, about 5% of an average week. It expects about 69 reports a week, 276 over the next 4 weeks, with a likely range of 260 to 292. These are estimates, not guaranteed counts.
Source: forecast/insights.md

**7. What if the AI gets it wrong?** (petroblyn)
Reports it is unsure about are marked for a person to check, urgent or unclear reports go to a supervisor for approval, and every decision is logged with a reason. The model card says not to use it to close or reject reports without a person.
Source: docs/one_page_explanation.md, governance/model_cards/workflow.md, workflow/approvals.py

**8. Can it predict a surge like the January one?** (Tshepo)
Not in advance. It has only one year of history, so it cannot learn yearly patterns such as the busiest week (12 January 2026, 132 reports, a summer water crisis). A surge like that would show up quickly once it starts. Water is the only service with a rising trend, about 1 extra report a week (+8%).
Source: docs/one_page_explanation.md, forecast/insights.md

**9. Have the translations been checked?** (Thembelihle)
Not yet. The non-English test examples are marked CHECK and have not been verified by fluent speakers. This is an open risk. The plan is for fluent speakers to review and sign off the examples using the translation review sheet, then retest.
Source: governance/risk_register.csv (R6-03), governance/translation_review.csv

**10. Are the repair deadlines real?** (petroblyn)
No. They are assumptions (24 hours for the most urgent reports up to 14 days for the least urgent), not real crew capacity. Service staff would need to review them before real use.
Source: governance/model_cards/workflow.md

## Bias and fairness

**11. Is it fair to every area?** (Thembelihle)
We can't claim that yet. Deadlines depend on urgency, not on the ward. But our fairness check on the synthetic data found urgent reports waiting longer in some wards (median 44.30, 37.45 and 36.85 hours in Tsutsumani, Setswetla and Far East Bank, against a 35.3-hour screening limit), and ranking areas only by number of reports could send more crews to already busy wards. Both are recorded as open risks, with proposed fixes: weigh urgency and reports per household, keep a minimum service level for every ward, and review ward-level results.
Source: governance/risk_register.csv (R6-04, R6-05), docs/week6_risk_report.md, workflow/routing.py

**12. Does a quiet area mean fewer problems?** (Tshepo)
No. Tsutsumani has the fewest reports (236 of 3,994), but quieter areas may simply report less, for example because of airtime costs or less trust that reports are acted on. The hotspot map shows where reports are concentrated in this dataset; it does not show where problems are worst.
Source: hotspots/insights.md, docs/one_page_explanation.md, docs/week6_risk_report.md

## Privacy and POPIA

**13. How do you protect residents' personal details?** (Thembelihle)
A masking function hides names, phone numbers, ID numbers, emails and house numbers before text goes into the decision log or an email, and it is covered by automated tests. A resident's email address is never saved in the ticket, the log or the saved emails. Two limits: masking is pattern-based and can miss unusual formats or names without a title, and the public dashboard still shows report text unmasked. That is safe only because the data is synthetic, and it must be fixed before any real report is used.
Source: governance/privacy.py, governance/test_privacy.py, governance/risk_register.csv (R3-02), docs/week6_risk_report.md

**14. Is it POPIA compliant?** (Thembelihle)
Not yet, and we say so. Our POPIA checklist scores 10 principles: 9 are only partly met and 1 is not met, because residents can't yet see or correct their reports. The decision log deletes rows older than 12 months, but the checklist still rates retention as partly met. These gaps must be fixed before any real resident data is used.
Source: governance/popia_checklist.md, docs/week6_risk_report.md

**15. Can a resident see or correct their report?** (Thembelihle)
No, this has not been built. It is listed as a safeguard needed before real data is used.
Source: governance/popia_checklist.md, docs/week6_risk_report.md

## Cost and rollout

**16. What does it cost to run?** (Dikeledi)
The demo runs on a free hosting service (Streamlit Community Cloud). We haven't costed a real deployment. A real one would need a database, controlled access, mail settings and an approved way to contact residents; we have not priced these.
Source: docs/deployment.md

**17. What happens if the live site restarts?** (Dikeledi)
Reports submitted and decisions made on the live site are lost when the app restarts or rebuilds, and the 10 example tickets load again. That is fine for a demo but means it is not a permanent case-management system. The app also sleeps when unused, so we wake it about 15 minutes before presenting.
Source: docs/deployment.md

**18. What happens with real data?** (Thembelihle)
Before any real reports are used: report text must be masked on screen, residents need a way to see and correct their reports, translations need fluent-speaker review, and the findings must be re-checked on a sample of real reports.
Source: docs/week8_presentation_script.md (responsible AI section), docs/one_page_explanation.md

## Technical choices

**19. How do you know it works?** (petroblyn)
Three ways: automated tests (246 passed when we ran them on a fresh copy of the project), the 30 tricky test reports for the sorter, and a backtest of the forecast on past weeks. All of this is on synthetic data.
Source: docs/technical_documentation.md, docs/one_page_explanation.md

**20. What happens if one step of the system fails?** (Dikeledi)
The report is not lost. A failed step still saves the ticket to the supervisor's approval queue with a note, so a person can check it.
Source: workflow/pipeline.py, governance/risk_register.csv (R4-08)

## What next

**21. What would you do next?** (Andile)
In order: test on an authorised sample of real reports once privacy safeguards are in place; have service staff review the routing and deadline rules; add resident access and correction and on-screen masking; have fluent speakers review translations; move from the demo to persistent storage. Until then Report Radar is a synthetic-data demonstration, not a tool for real resident decisions.
Source: docs/week8_presentation_script.md (the ask), docs/week6_risk_report.md, docs/deployment.md

**22. What do you need from us?** (Andile)
An operational sponsor to help define a controlled next step: an authorised, representative sample for evaluation, staff review of the routing and deadline rules, and agreement on what evidence would justify a limited pilot.
Source: docs/week8_presentation_script.md (the ask)
