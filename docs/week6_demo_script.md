# Report Radar: Week 6 demo script (AI Risk & Compliance)

**5 minutes, then questions.** Each person presents one risk they found: who it harms, the evidence, and what we did. We end with a 1-minute ethics discussion.

**Before the demo:** run `python run_all.py` so the decision log is filled, then `streamlit run dashboard/app.py`, and open the **Risk & compliance** tab. Have `docs/week6_risk_report.md` open in a second window.

| Time | Speaker | Shows | Says (about 45 seconds each, in your own words) |
| --- | --- | --- | --- |
| 0:00-0:30 | **Role 5: Andile Khoza** | Risk & compliance tab: the summary sentence and "The three biggest risks" | "This week we asked: where could Report Radar be unfair, unsafe with personal data, or trusted too much? We found 19 risks; 10 are high. Everything is in one register here, and a manager can download it as a report." *(click Download risk evaluation report)* |
| 0:30-1:15 | **Role 2: Tshepo Tleane** | "Do some areas wait longer?" chart | "Urgent reports wait a median of 44 hours in Tsutsumani, but 24 in Old Alexandra. Three areas break our rule that no area should wait more than 1.5 times the fastest. Worse, our own hotspot map sends crews to the busiest areas, so quiet areas can wait longer and report even less: a feedback loop." |
| 1:15-2:00 | **Role 1: petroblyn** | "Does the system work equally well in every language?" table | "We wrote the same 10 problems in six South African languages. Before, the other five languages were sorted right only 0 to 30% of the time; English was 100%. We added phrases and made elderly, disabled and pregnant residents raise urgency. It's 100% on our test set now, but that's optimistic: new wording still slips, and a fluent speaker still has to check the translations." |
| 2:00-2:45 | **Role 3: Thembelihle** | `governance/popia_checklist.md`, then run the masking command below in a terminal | "Residents write names and phone numbers in their reports. Our masking function hides them before anything is logged or sent to an AI company. Against POPIA's 10 principles, 9 are partly met and 1 is not: residents can't yet see or correct their reports." |
| 2:45-3:30 | **Role 4: Dikeledi** | "Latest decisions the system made", then the "Transparency notes" expander | "Every decision is now recorded: each sorted report, forecast and hotspot run, with the reason and the rules version. Personal details are hidden, and rows are deleted after 12 months. Each tab has a plain-language 'How this was decided' note, and each model has a one-page card saying how accurate it is." |
| 3:30-4:00 | **Role 5: Andile Khoza** | "All risks" table, filtered to Status = Open | "We are honest about what is not fixed. The biggest one: our public dashboard still shows report text word for word. That's fine with synthetic data, but we won't use real reports until it's masked and behind a login." |
| 4:00-5:00 | **Everyone: ethics discussion** | `docs/week6_risk_report.md`, section "Ethical reasoning" | See below. |

**Masking command for Role 3** (run from the repo folder; it uses made-up details only):

```bash
python -c "from governance.privacy import mask_personal_info as m; print(m('No water at house 23. Call Mrs Dlamini on 082 123 4567'))"
```

It prints: `No water at house [HOUSE_NO]. Call [NAME] on [PHONE]`

## Ethics discussion (1 minute)

**Question we answer: which risk worries us most, and why?**

- **Tshepo:** "Unequal service between areas. A wrong urgency score harms one person and can be corrected. A feedback loop harms whole communities slowly, and the data makes it look smaller every time."
- **petroblyn:** "And language bias feeds that loop: if the system doesn't understand you, you stop reporting."
- **Thembelihle:** "Privacy is the one that could cause harm overnight if real data were used, so we put a hard rule on it."
- **Andile (closing):** "So our rule is: no real resident data until report text is masked on the dashboard, residents can correct their reports, and every language we claim to support is checked by a fluent speaker."

## Likely questions

- *Why is the classifier 100% now, but you still list language bias as a top risk?* The 100% is on the reports we wrote the phrases for. "Ku hava mati" (Xitsonga, no water) still gets a lower urgency than the same problem in English.
- *How did you score the risks?* Likelihood × impact, each from 1 to 5; 15 or more counts as high. We scored our own system, so we've asked for an outside review (R5-03).
- *Why not just remove the hotspot map?* Busy areas really do need more capacity. The fix is to rank by urgency and households, not raw report counts, and to guarantee a minimum service level for every area.
- *Is anything personal in the decision log?* Summaries are masked and cut to 80 characters before writing. Masking works by patterns, so it can miss unusual formats; that's in the register as R3-02.

## If something goes wrong

- **The "Latest decisions" section is empty:** `run_all.py` wasn't run; the decision log is created on each run, not stored in the repo. Run it (about 20 seconds) and refresh.
- **Running long:** shorten the role parts to one sentence each, but keep the ethics discussion: it carries the 60% "ethical reasoning" mark.
