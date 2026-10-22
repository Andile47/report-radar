# Forecast (Role 1: Forecast Lead)

Answers the question **"how many reports should we expect next week and next month?"** It looks at past weekly report volume and predicts the next 4 weeks, so teams can see a surge coming and plan their workload.

## How to run

From the repo root:

```bash
python forecast/forecast.py   # builds the forecast and writes the files below
pytest forecast               # runs the tests
```

Re-run the script whenever `data/reports.csv` changes. The dashboard picks up `output.csv` automatically.

## How it works, step by step

1. **Weekly counts.** Reports in `data/reports.csv` are counted per week (Monday to Sunday).
2. **Partial weeks removed.** The first and last weeks only contain a few days of data, so they would look like a sudden drop. They are left out.
3. **Four simple models are compared:**
   - *naive*: next week looks like last week
   - *moving average*: next week looks like the average of the last 4 weeks
   - *linear trend*: a straight line fitted to the last 12 weeks, extended forward (scikit-learn `LinearRegression`)
   - *moving average + trend*: start from the 4-week average and add the trend line's weekly change for each week ahead
4. **Backtest.** Each model is tested on the last 12 weeks. We pretend to stand at each week, forecast 4 weeks ahead using only earlier data, and measure how far off it was (mean absolute error, MAE, in reports per week).
5. **Best model wins.** The model with the lowest MAE makes the real forecast. The same is done for every category separately.
6. **Projected workload.** The forecast for each week is shown with a likely range (forecast plus or minus the MAE) and a total for the next 4 weeks, which is roughly the next month.
7. **Insights.** The result is turned into 3 plain sentences: next week and next month, which category is driving any change (with a surge alert if the total or a category is forecast to rise 15% or more above the last 4 weeks), and how accurate the forecast usually is.
8. **Chart.** Past weekly volume, the 4-week moving average, the trend line and the forecast with its likely range are drawn with matplotlib.

## Output files

| File | Contents |
| --- | --- |
| `projected_workload.csv` | **Hand-over table:** expected reports for each of the next 4 weeks, likely range, and the 4-week total |
| `forecast_chart.png` | **Hand-over chart:** past volume, moving average, trend line and forecast |
| `insights.md` | **Hand-over text:** the 3 sentences plus the workload table, for the dashboard's Forecast tab (replaces the dashboard's "TODO (Role 2)" note) |
| `output.csv` | `week_start, actual, forecast`, the dashboard contract. History rows have `actual`; the next 4 weeks have `forecast`. The last history week has both so the chart lines join. |
| `output_by_category.csv` | Same as above per category, plus the `model` chosen for it |
| `metrics.json` | MAE of every model, the selected model, and accuracy per category |

## Current result

On the synthetic data (51 full weeks, 27 Oct 2025 to 12 Oct 2026):

- The plain 4-week moving average was most accurate. It is off by about 4 reports a week (5% of an average week).
- The other models scored worse: naive 5.0, moving average + trend 6.4, linear trend 7.2.
- Expect about **69 reports next week** and **about 276 over the next 4 weeks** (likely 260-292), level with recent weeks. No surge is flagged.
- Water is the main rising category, at about +1.3 reports a week (+8%). It is the one category where moving average + trend was the most accurate model.

The predictions sit within the range of recent weeks (61-78 a week) and never go below zero.

## Limitations of a simple model

- **One year of data only.** Seasonal patterns, such as the January peak of 132 reports, can't be learned yet. With two or more years, a seasonal model would be worth adding.
- **Flat or straight-line forecasts.** These show the expected level, not week-to-week spikes from storms, long outages or cable theft.
- **Recent weeks dominate.** A sudden change in the last month moves the forecast quickly; an older pattern is ignored.
- **The likely range is a rough guide.** It is based on past average error, not a statistical confidence interval. The monthly range assumes every week misses in the same direction, so it is on the wide side.
- **Synthetic data.** Accuracy on real reports may differ.
