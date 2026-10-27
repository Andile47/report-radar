# Model card: Workload forecast

*Report Radar · Week 6 · last reviewed 27 Oct 2026 · rules version `forecast-2026.10`*

## What it is for

It predicts how many citizen reports will arrive each week for the next 4 weeks, so managers can plan staff before a surge. It answers "how busy will we be?", not "what will go wrong where?".

**Don't use it for:** judging individual staff or areas, setting budgets for a full year, or predicting one-off events such as a storm.

## Data it uses

- `data/reports.csv`: 3,994 **synthetic** reports from Alexandra, 22 Oct 2025 to 21 Oct 2026.
- Only the date of each report is used: reports are counted per week (Monday to Sunday).
- The first and last weeks are left out because they are incomplete, which leaves 51 full weeks (27 Oct 2025 to 12 Oct 2026).

## How it works, in plain words

1. Count reports per week.
2. Try four simple methods: "same as last week", "average of the last 4 weeks", "a straight-line trend over the last 12 weeks", and "4-week average plus the trend".
3. Test each one on the last 12 weeks, as if we didn't know what happened, and measure how far off it was.
4. Use the most accurate method for the next 4 weeks. The same is done for each problem type.

## How accurate it is

| Method | Average error (reports a week) |
| --- | --- |
| **4-week average (chosen)** | **4.0**, about 5% of an average week (77 reports) |
| Same as last week | 5.0 |
| Average plus trend | 6.4 |
| Straight-line trend | 7.2 |

By problem type, the average error ranges from 1.6 (rubbish) to 3.5 (water). The dashboard shows a "likely range" of the forecast plus or minus 4 reports a week.

## Known limits and risks

- **Can't see surges coming.** With only one year of data it can't learn yearly patterns. The January water surge (132 reports in one week, 1.8 times a normal week) would not be predicted ahead of time.
- **Flat forecasts.** The 4-week average gives the same number for every week ahead (currently 69), so it shows the level, not the week-to-week ups and downs.
- **Counts reports, not problems.** Areas that report less look quieter than they are, and the forecast inherits that bias (see the area fairness analysis).
- **Over-trust.** A precise-looking number such as "276 reports" can be taken as certain. Always read it with its likely range (260 to 292).
- **Synthetic data.** Accuracy on real reports is unknown until it is tested on them.

## How decisions are recorded

Every run adds one row to the decision log (`governance/logs/decisions.csv`) with the forecast, the method chosen and the errors of all four methods.

## Who to contact

Forecast Lead: Dikeledi. Code: `forecast/forecast.py`. Details: `forecast/README.md`.
