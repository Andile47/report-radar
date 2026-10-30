# Classifier Bias Check

## What We Tested

The test set contains 70 made-up reports: 10 common service problems in each of English, isiZulu, Sesotho, Sepedi, Xitsonga, and Afrikaans, plus 10 English reports mentioning elderly, disabled, or pregnant residents. Every non-English test ID starts with `CHECK-` because a fluent speaker still needs to verify the wording. No real personal data is used.

The checker calls `process_report()` for every row and calculates exact category accuracy, exact urgency accuracy, and the share of urgency predictions no more than one point from the expected score. The before file records the original classifier; the after file records the classifier with additional category and urgency phrases, Unicode-aware phrase matching, and expanded vulnerability terms.

## Results

| Language | Reports | Before category | Before urgency | Before within 1 | After category | After urgency | After within 1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Afrikaans | 10 | 10% | 10% | 60% | 100% | 100% | 100% |
| English | 10 | 100% | 70% | 80% | 100% | 100% | 100% |
| Sepedi | 10 | 0% | 10% | 60% | 100% | 100% | 100% |
| Sesotho | 10 | 0% | 10% | 60% | 100% | 100% | 100% |
| Xitsonga | 10 | 10% | 20% | 70% | 100% | 100% | 100% |
| isiZulu | 10 | 30% | 30% | 60% | 100% | 100% | 100% |

| Group | Reports | Before category | Before urgency | Before within 1 | After category | After urgency | After within 1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Language examples | 60 | 25% | 25% | 65% | 100% | 100% | 100% |
| Vulnerable-resident examples | 10 | 100% | 20% | 80% | 100% | 100% | 100% |

These are results on a small, deliberately curated set, not a measure of real-world accuracy. The after phrases were added to cover these sample reports, so the 100% result must not be interpreted as proof that the classifier understands these languages generally. The translation checks are still pending.

## Changes and Limits

The classifier now includes phrase keywords for the tested service problems in the six listed languages. It recognizes additional terms for elderly, disabled, wheelchair-using, and pregnant residents when applying the existing urgency increase. Text normalization and phrase boundaries now preserve Unicode letters so words containing characters such as `š` can be matched.

The specific report `Wheelchair user can't get home safely` now receives urgency 4 and is sent for human review: the safety phrase supplies a level-3 signal, the wheelchair term raises it by one, and no service category is named. A vulnerability term alone still does not increase a report that has no recognized urgency signal.

Keyword rules cannot cover every spelling, dialect, typo, synonym, code-switch, or way of describing a problem. They also cannot reliably infer severity from context, negation, duration, or consequences when the relevant words are absent. Adding a few phrases for these languages does not support other languages or guarantee that a phrase has been translated correctly.

## Human Review

- A result with category `other` has `review_required: true` and should be checked by a person.
- Ask a fluent speaker to verify every `CHECK-` test description before treating it as an approved translation or expanding production use.
- Have a person check reports with unfamiliar wording, mixed languages, conflicting problems, or a potentially dangerous situation whose urgency seems understated, even if a category was assigned. `review_required` is currently based on category `other`; a low or incorrect urgency by itself does not trigger it.
- Keep a human escalation path for urgent safety decisions. Do not use the keyword score as a substitute for assessing the resident's situation.

The before and after measurements are saved in `governance/bias_results_before.csv` and `governance/bias_results_after.csv`. The test examples are in `governance/bias_test_reports.csv`.