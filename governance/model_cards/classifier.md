# Model card: Report classifier (problem type and urgency)

*Report Radar · Week 6 · last reviewed 2 Nov 2026 · rules version `classifier-2026.10`*

## What it is for

It reads what a resident wrote and decides two things: the **type of problem** (water, electricity, roads, sewage and toilets, rubbish, streetlights) and the **urgency** from 1 (cosmetic) to 5 (danger to life). Reports it can't sort confidently are marked **"needs a person to check"** instead of being guessed.

**Don't use it for:** making final decisions without a person, refusing a report, or ranking residents.

## Data it uses

- Only the report's description text.
- The keyword lists were built from the 3,994 **synthetic** reports in `data/reports.csv`, which use about 44 different wordings, plus phrases in isiZulu, Sesotho, Sepedi, Xitsonga and Afrikaans added in Week 6 from a curated test set (`governance/bias_test_reports.csv`).

## How it works, in plain words

1. **Tidy the text** and fix small typos ("watr" becomes "water").
2. **Problem type:** each keyword has points. Specific words such as "sewage" or "pothole" score 3; general words such as "road" score 1. The type with the most points wins. A tie, no keywords, or two strong problems in one report go to "needs a person to check".
3. **Urgency:** each danger phrase has a level ("live wire" = 5, "no water" = 3, "small crack" = 1). The highest level found is used, plus one if a school, clinic, creche or children are mentioned, or an elderly, disabled or pregnant resident.
4. **Reason:** every result lists the words that decided it, so a person can see why.

## How accurate it is

| Test | Result |
| --- | --- |
| The dataset's own reports (3,994) | 100% right problem type; urgency exactly right 85%, within one level 99.7%. **Optimistic**: the keywords were built from these same reports. |
| 30 tricky test reports (typos, slang, isiZulu, vague or mixed) | **4 of 30** problem types wrong; urgency exactly right 14 of 30, and off by 2 or more levels 5 of 30. |
| 70-report bias test set (6 languages plus vulnerable residents) | Before the Week 6 changes: right problem type for 100% of English reports but only 0-30% in the other five languages. After: 100% in every language. **Optimistic**: the new phrases were written to cover these same reports, and the translations are still waiting for a fluent speaker to check them. |

## Known limits and risks

- **Language bias is reduced, not solved.** Week 6 added phrases in five more South African languages, and "there is no water" in Sesotho, isiZulu, Sepedi and Afrikaans now gets the same urgency as in English (3). But wording outside the curated set is still under-scored: "Ku hava mati" (Xitsonga, no water) and "Ha ho motlakase" (Sesotho, no electricity) get urgency 2, and languages not covered at all go to "needs a person to check". The translations have not yet been checked by fluent speakers.
- **Vulnerable people: partly fixed.** Elderly, disabled and pregnant residents now raise urgency ("Gogo is 80 and has had no water for 3 days" is now 4), but only when the report uses one of the listed words.
- **New wording is missed.** Danger described in words that aren't on the list gets a low urgency, e.g. "sparks flying from the wires near the creche" scored 2 instead of 5.
- **Over-trust.** Managers may treat the urgency score as a fact. It is a first sort, and a person should check anything that looks wrong.
- **The LLM version is untested.** `intake/llm_classifier.py` would send residents' words to an outside company. Personal details are now masked with `governance/privacy.py` before anything is sent, and nothing is sent if masking isn't available, but the masking is pattern-based and can miss unusual formats.

## How decisions are recorded

Every classified report adds one row to the decision log (`governance/logs/decisions.csv`): the report ID, a masked 80-character summary, the problem type, urgency, needs-review flag, the reason, and the rules version.

## Who to contact

Intake and Urgency Lead: petroblyn. Code: `intake/classifier.py`. Details: `intake/README.md`, `intake/test_summary.md` and `governance/classifier_bias.md`.
