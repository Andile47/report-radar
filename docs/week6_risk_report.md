# Report Radar: Week 6 risk evaluation report

*AI Risk & Compliance Layer · 2 November 2026 · all data in this project is synthetic*

## Summary

Report Radar sorts citizen reports from Alexandra, Johannesburg, forecasts next month's workload and shows where problems cluster. This week we checked where it could be unfair, unsafe with personal information, or trusted too much.

**We found 19 risks; 10 are high (score 15 or more out of 25).** Four are now mitigated and one is closed; 14 are still open or in progress. The three that worry us most:

1. **Quieter areas wait longer for urgent repairs.** Urgent reports take a median of 44 hours to fix in Tsutsumani, against 24 hours in Old Alexandra, and our own hotspot map could make this worse.
2. **Residents who don't write in English can get a lower urgency.** Before this week, the same 10 problems written in five other South African languages were sorted correctly only 0-30% of the time, against 100% in English.
3. **Personal information in report text.** Residents may write names, phone numbers and addresses. Until this week, that text could be logged or sent to an outside AI company unmasked, and the public dashboard still shows it word for word.

We fixed what we could in one week, and we say plainly below what is still not fixed.

## How we assessed the risks

Each of the five team members audited the part of Report Radar they built, measured what they could on our data, and added risks to a shared register (`governance/risk_register.csv`). Every risk is scored for **likelihood** and **impact** from 1 to 5; the score is likelihood × impact. The full register, with evidence and owners, is in the dashboard's **Risk & compliance** tab, which can also download it as a report.

| Area | Risks | High (15+) | Owner |
| --- | --- | --- | --- |
| Classifier bias (language, vulnerable residents) | 3 | 3 | Role 1: petroblyn |
| Area fairness | 3 | 3 | Role 2: Tshepo Tleane |
| Privacy and POPIA | 4 | 2 | Role 3: Thembelihle |
| Logging and transparency | 5 | 1 | Role 4: Dikeledi |
| Dashboard and reporting | 4 | 1 | Role 5: Andile Khoza |

## Finding 1: unequal service between areas

**What we found.** Median time to fix urgent reports (urgency 4-5), by area:

| Area | Reports | Urgent median (hours) | Breaks the 1.5× rule? |
| --- | --- | --- | --- |
| Tsutsumani | 233 | 44.3 | Yes |
| Setswetla | 375 | 37.5 | Yes |
| Far East Bank | 564 | 36.9 | Yes |
| East Bank | 1,008 | 30.5 | No |
| Pan Africa | 626 | 25.9 | No |
| Old Alexandra | 1,188 | 23.6 | No |

We proposed a screening rule: no area's urgent reports should wait more than 1.5 times as long as the fastest area's (35.3 hours here). Three areas break it.

**Why it matters.** Our hotspot map ranks areas by how many reports they send. If crews follow it, busy areas get faster service, quiet areas wait longer, residents there lose trust and report less, and they look even quieter next time. This is a **feedback loop**: the system could deepen an inequality it was meant to help with.

**What we did.** Measured it, set a rule that flags it, and explained it on the dashboard and in the hotspot model card: "the ranking shows where most reports come from, not where most problems are". Every hotspot run is now logged with that note.

**What remains.** The hotspot ranking itself still uses raw counts. A fair version would weight by urgency and by households per area, but we have no real census figures, and the household numbers in our analysis are clearly labelled assumptions (R6-06).

## Finding 2: language and vulnerable-resident bias in the classifier

**What we found.** We wrote the same 10 problems in English, isiZulu, Sesotho, Sepedi, Xitsonga and Afrikaans, plus 10 reports about elderly, disabled or pregnant residents.

| | Before Week 6 | After Week 6 |
| --- | --- | --- |
| English: right problem type | 100% | 100% |
| Other five languages: right problem type | 0-30% | 100% |
| Vulnerable residents: urgency exactly right | 20% | 100% |

**Why it matters.** A report the system doesn't understand gets the default urgency of 2, so a resident who writes "Ha ho na metsi" (Sesotho for "there is no water") would wait longer than one who writes in English. That is unfair treatment based on language.

**What we did.** Added phrases in five more languages, made elderly, disabled and pregnant residents raise urgency, and send reports the system can't understand to a person instead of guessing.

**What remains, honestly.** The "after" score of 100% is on the same reports the new phrases were written for, so it is optimistic. Wording outside that set still slips: "Ku hava mati" (Xitsonga, no water) and "Ha ho motlakase" (Sesotho, no electricity) still get urgency 2, and "sparks flying from the wires near the creche" gets 2 instead of 5. The translations still need a fluent speaker to check them (R6-03). Keyword rules can't fully solve this; a person must review uncertain reports.

## Finding 3: personal information and POPIA

**What we found.** Residents write free text, which can contain names, phone numbers, ID numbers and addresses. The text was being stored in the decision log, could be sent to an outside LLM, and is shown on the public dashboard.

**What we did.**

- A masking function (`governance/privacy.py`) replaces phone numbers, ID numbers, emails, house numbers and names with placeholders such as `[PHONE]`. It is tested with made-up examples.
- The decision log masks every summary before writing, and deletes rows older than 12 months.
- The optional LLM classifier now masks text before sending it, and sends nothing if masking isn't available.
- A data card and a POPIA checklist record what data we hold and why. Of 10 principles, 9 are partly met and 1 is not met: residents can't yet see or correct their reports.

**What remains.** Masking works by patterns, so it can miss unusual formats or names without a title (R3-02). The public dashboard still shows report text unmasked (R5-01). That's safe only because the data is synthetic, and it **must** be fixed before any real report is used.

## Finding 4: transparency and over-trust

**What we found.** Before this week, nothing recorded what Report Radar decided or why. Managers could also take a single number such as "69 reports next week" as certain.

**What we did.**

- Every sorted report, forecast and hotspot run is logged with its reason and rules version (R4-01, mitigated).
- One-page model cards for the forecast, classifier and hotspots state their accuracy and limits: the forecast is usually within about 4 reports a week, and the classifier gets 4 of 30 tricky reports wrong.
- "How this was decided" notes explain each dashboard tab in plain language, and every forecast is shown with its likely range.

**What remains.** The summary box still leads with single numbers (R5-02), and our register was scored by the same team that built the system (R5-03). An outside review would make it stronger.

## Ethical reasoning: which risk matters most?

We rank **unequal service between areas** first, even though several risks share the top score of 20. A privacy breach or a mis-sorted report harms one resident at a time and can be noticed and corrected. A feedback loop harms whole communities slowly and quietly: the data makes the problem look smaller every time, so nobody is prompted to act. It also hits the areas that already have the least voice. The language bias feeds the same loop, because residents who aren't understood report less.

We also agree that **no real resident data should go into Report Radar** until three things are done: report text is masked on the dashboard, residents can see and correct their reports, and a fluent speaker has checked every language the system claims to support. A tool meant to help a municipality respond fairly must not become a new way to overlook people.

## Next steps

| Action | Risk | Owner |
| --- | --- | --- |
| Mask report text on the dashboard and add a login before using real data | R5-01, R3-01 | Role 5 + Role 3 |
| Weight the hotspot ranking by urgency and verified household counts | R6-04, R6-05 | Role 2 |
| Have fluent speakers check every translated phrase | R6-01, R6-03 | Role 1 |
| Add a way for residents to see and correct their reports | R3-04 | Role 3 |
| Ask the facilitator or another team to review this register | R5-03 | Role 5 |

*Sources: `governance/risk_register.csv`, `governance/area_fairness.md`, `governance/classifier_bias.md`, `governance/popia_checklist.md`, `governance/model_cards/`.*
