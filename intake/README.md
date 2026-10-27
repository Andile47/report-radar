# Intake and Urgency (Role 4: Intake and Urgency Lead)

When a report comes in, this module decides **what type of problem it is** and **how urgent it is** (1 to 5). It is built two ways so they can be compared: keyword rules (`classifier.py`) and an LLM prompt (`llm_classifier.py`).

## How to run

From the repo root:

```bash
python intake/classifier.py   # classify every report in data/reports.csv
python intake/evaluate.py     # test on the 30 tricky reports, count mistakes
pytest intake                 # unit tests
```

Both scripts work from any folder.

## How the keyword classifier works

1. **Clean the text.** Lower-case it, and fix small typos by matching words to the keyword list ("watr" → "water"). Only words that share the first letter are changed, so "whole" doesn't become "hole".
2. **Category.** Every keyword has points. Specific phrases such as *sewage*, *pothole* or *standpipe* score 3; general words such as *road* or *water* score 1. The category with the most points wins. So "Pothole filled with water" is roads (3 vs 1), not water.
3. **Needs review.** A tie, no keywords at all, a thank-you message, or two strong problems in one report ("no water and no electricity") gives category `other` with `review_required = True`, so a person looks at it instead of the system guessing.
4. **Urgency.** Danger phrases have levels: *live wire*, *open manhole*, *raw sewage*, *burst pipe* = 5; *sparking*, *brown water*, *flooding* = 4; *no water*, *not working*, *pothole* = 3; *leaking*, *flickering* = 2; *small crack*, *on all day* = 1. The highest level found is used, plus one when a school, clinic, creche or children are mentioned. With no urgency words, the default is 2.
5. **Reason.** Each result lists the words that decided it, e.g. `roads: pothole | level 3: pothole`.

## Examples

| Report | Category | Urgency | Reason |
| --- | --- | --- | --- |
| Burst pipe flooding 4th Avenue, water running down the road | water | 5 | water: burst pipe, water · level 5: burst pipe |
| Pothole filled with water after the rain, taxis swerving | roads | 3 | roads: pothole, taxis · level 3: pothole |
| Akukho ugesi since last night, 7th Avenue | electricity | 3 | electricity: ugesi · level 3: ugesi, since last night |
| Small crack and sinking tar near the school gate | roads | 1 | roads: tar · minor: small crack |
| Water outage affecting the whole block, clinic nearby has no water | water | 5 | water: water outage, no water · level 5: whole block |
| No water and no electricity since the storm | other (review) | 3 | tie between water and electricity |

## Results

**On the dataset (3,994 reports):** the category agrees with the dataset label 100% of the time, urgency is exactly right 85% of the time, and within one level 99.7% of the time. These scores are **optimistic**: the keywords were tuned on these same descriptions, and the dataset only has 44 different description patterns once street names are removed.

**On 30 tricky test reports** (`test_reports.csv`: typos, slang, isiZulu, vague and mixed reports), the honest measure:

| Version | Category wrong | Urgency exactly right | Urgency off by 2+ levels |
| --- | --- | --- | --- |
| Keyword classifier | **4 / 30** | 15 / 30 | 5 / 30 |
| LLM classifier | not run yet: needs an API key | | |

The tests were written before the keywords were tuned, so they weren't used to fit the rules. Full results are in `test_summary.md` and `test_results.csv`. Main weaknesses:

- **Words not in the list are missed.** *"Dead dog on the pavement"* and *"Road caved in"* aren't recognised, because "dead dog" and "caved in" aren't keywords.
- **Danger described in new words gets low urgency.** *"Sparks flying from the wires near the creche"* scores 2 instead of 5.
- **"and" is over-read as two problems.** *"Sewer pipe burst and it stinks"* goes to review even though it's one sanitation problem.

These are the cases where the LLM version should do better. When the team has an API key, run `python intake/evaluate.py` again: it adds the LLM row to the table automatically.

## LLM version

`llm_classifier.py` sends the report with a prompt that defines the 6 categories, the 1-5 urgency scale with examples, local slang and isiZulu. It asks for JSON only: `{"category": ..., "urgency": ..., "reason": ...}`. The reply is checked: the category must be one of ours and urgency 1-5. If the model is unavailable or replies badly, the report falls back to the keyword classifier, so intake never stops.

Setup: `pip install anthropic`, then set `ANTHROPIC_API_KEY` (and optionally `LLM_MODEL`, default `claude-haiku-5-5`). To use a different LLM, pass your own `ask` function: `classify_with_llm(text, ask=my_function)`.

## Output files

| File | Contents |
| --- | --- |
| `data/reports_clean.csv` | Reports with spaces tidied, empty descriptions and repeated IDs removed |
| `data/reports_classified.csv` | Clean reports plus `predicted_category`, `predicted_urgency`, `review_required` and `reason`. The original `category` and `urgency` columns are kept for comparison |
| `test_reports.csv` | The 30 tricky test reports with the expected answers |
| `test_results.csv`, `test_summary.md` | Results of `evaluate.py` |

## Limitations

- Keyword rules only know the words they were given; new wording needs new keywords.
- The 30 test reports and their expected answers were written by one person, so the error count is a guide, not a precise accuracy. Ask a teammate to add 10 more reports they wrote themselves.
- Urgency is a judgement; two people can reasonably disagree by one level.
