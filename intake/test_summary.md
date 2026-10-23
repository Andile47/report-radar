# Intake classifier: results on 30 tricky test reports

| Version | Category wrong | Urgency exactly right | Urgency off by 2+ levels |
| --- | --- | --- | --- |
| Keyword classifier | 4 / 30 | 15 / 30 | 5 / 30 |

LLM classifier not run: set ANTHROPIC_API_KEY and `pip install anthropic`, then run this script again to add its row.

## Keyword classifier: wrong categories

| Test | Report | Expected | Got | Why |
| --- | --- | --- | --- | --- |
| T12 | Its pitch black on our road at night, very dangerous | streetlights | roads | roads: road |
| T19 | Sewer pipe burst and it stinks | sanitation | other | two problems reported (sanitation and water) |
| T22 | Drain overflowing onto the road | sanitation | other | tie between roads and sanitation |
| T26 | Dead dog on the pavement | refuse | other | no service keywords found |

## Keyword classifier: urgency off by 2 or more

| Test | Report | Expected | Got |
| --- | --- | --- | --- |
| T05 | Water coming out of the electricity box on the pole | 5 | 2 |
| T06 | Brown smelly water from my tap | 4 | 2 |
| T08 | Sparks flying from the wires near the creche | 5 | 2 |
| T14 | Massive hole in the road swallowed a car tyre | 4 | 2 |
| T18 | Road caved in near the river after the rain | 5 | 2 |
