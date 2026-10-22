# Forecast (Role 1: Forecast Lead)

Predicts how many citizen reports will arrive each week for the next 4 weeks, so teams can see a surge coming and plan their workload.

## How to run

From the repo root:

```bash
python forecast/forecast.py   # builds the forecast and writes the files below
pytest forecast               # runs the tests
```

Re-run the script whenever `data/reports.csv` changes. The dashboard picks up `output.csv` automatically.

## How it works

1. **Weekly counts.** Reports in `data/reports.csv` are counted per week (Monday to Sunday).
2. **Partial weeks removed.** The first and last weeks only contain a few days of data, so they would look like a sudden drop. They are left out.
3. **Three simple models are compared:**
   - *naive*: next week looks like last week
   - *moving average*: next week looks like the average of the last 4 weeks
   - *linear trend*: a straight line fitted to the last 12 weeks, extended forward (scikit-learn `LinearRegression`)
4. **Backtest.** Each model is tested on the last 12 weeks. We pretend to stand at each week, forecast 4 weeks ahead using only earlier data, and measure how far off it was (mean absolute error, MAE, in reports per week).
5. **Best model wins.** The model with the lowest MAE makes the real forecast. The same is done for every category separately.
6. **Insights.** The forecast is turned into 2-3 plain sentences, with a surge alert if the total or any category is forecast to rise 15% or more above the last 4 weeks.

## Output files

| File | Contents |
| --- | --- |
| `output.csv` | `week_start, actual, forecast`, the dashboard contract. History rows have `actual`; the next 4 weeks have `forecast`. The last history week has both so the chart lines join. |
| `output_by_category.csv` | Same as above per category, plus the `model` chosen for it |
| `metrics.json` | MAE of every model, the selected model, and accuracy per category |
| `insights.md` | Text for the dashboard's Forecast tab (replaces the dashboard's "TODO (Role 2)" note) |

## Current result

On the synthetic data (51 full weeks, 27 Oct 2025 to 12 Oct 2026), the moving average was most accurate. Its MAE is about 4 reports a week, which is 5% of an average week. The naive model scored 5.0 and the linear trend 7.2. The forecast is about 69 reports a week, level with recent weeks, and no surge is flagged. Water is the only category with a rising trend.

## Limitations

- Only one year of data, so seasonal patterns (e.g. the January peak) can't be learned yet. With two or more years, a seasonal model would be worth adding.
- Simple models give flat or straight-line forecasts. They show the expected level, not week-to-week spikes such as storms or long outages.
- The data is synthetic, so accuracy on real reports may differ.
