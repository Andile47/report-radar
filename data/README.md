# Data (Role 1: Data Lead)

All data here is **synthetic**: realistic fake citizen reports for Alexandra, Johannesburg. No real personal information is used.

## Files

| File | What it is |
| --- | --- |
| `reports.csv` | The shared dataset everyone builds on: 3,994 reports, 22 Oct 2025 to 21 Oct 2026 |
| `reports_sample.csv` | 20-row sample covering every category, ward and status, so teammates can start coding before the full data is ready |
| `generate_reports.py` | Script that generates synthetic reports with seasonality, rain, surges and unequal wards |
| `check_data.py` | Checks the dataset follows the agreed contract and that the surges, seasons and ward differences are there |
| `weekly_volume.png` | Reports per week, written by `check_data.py`, to confirm the surges visually |

## How to run

From the repo root:

```bash
python data/check_data.py                                   # check reports.csv, draw weekly_volume.png
python data/generate_reports.py --out data/reports_new.csv  # make a fresh synthetic dataset
python data/generate_reports.py --force                     # replace reports.csv (then run: python run_all.py)
```

The generator never overwrites `reports.csv` unless you pass `--force`, because the forecast, hotspots and dashboard are all built from it. The current `reports.csv` came from an earlier version of the generator. The committed script makes data with the same structure but different exact rows. With the same `--seed` and `--end` it gives the same result every time.

## Data dictionary (the agreed contract)

| Column | Type | Meaning |
| --- | --- | --- |
| `report_id` | text | Unique ID, e.g. `ALX-000001` |
| `timestamp` | date-time | When the report was made, `YYYY-MM-DD HH:MM:SS` |
| `category` | text | One of `water`, `electricity`, `roads`, `sanitation`, `refuse`, `streetlights` |
| `description` | text | What the citizen wrote. Includes isiZulu phrases and typos, e.g. *"Amanzi awekho since yesterday"*, *"no watr by us since 3 days"* |
| `ward_or_suburb` | text | Old Alexandra, East Bank, Pan Africa, Far East Bank, Setswetla, Tsutsumani |
| `latitude`, `longitude` | number | Location, scattered about 250 m around each ward's centre |
| `urgency` | 1-5 | 1 = cosmetic, 2 = low, 3 = medium, 4 = high (health, safety or many people affected), 5 = critical (danger to life, e.g. live wires, sinkholes) |
| `status` | text | `open`, `in_progress`, `escalated` or `resolved` |
| `hours_to_resolve` | number | Hours from report to fix. **Empty for the 528 reports that are not resolved yet**; this is expected, not missing data |

**Change to the original agreement:** the team first agreed 4 categories (water, roads, electricity, waste). The dataset uses 6: `refuse` instead of waste, plus `sanitation` and `streetlights`, because sewage and lighting faults are common reports that didn't fit the original 4. The forecast, hotspots, classifier and dashboard all use these 6.

## What makes it realistic

The `check_data.py` output for the current `reports.csv`:

- **Seasons:** water is 29% of summer reports vs 20% in winter; roads 23% vs 14% (more after summer rain).
- **Surges:** a typical week has 73 reports. The biggest surges are the January water crisis (132 reports in the week of 12 Jan 2026), a mid-June spike (102) and an early-December peak (101).
- **Unequal wards:** Old Alexandra (1,188) and East Bank (1,008) report about twice as often as Pan Africa (626) and Far East Bank (564), and about 5 times as often as Tsutsumani (233). This is needed for the Week 6 fairness check.
- **Daily rhythm:** most reports arrive 06:00-09:00 and 16:00-19:00.

## Limitations

- Synthetic patterns are what we put in, so they confirm the methods work, not what really happens in Alexandra.
- About 420 different descriptions are reused, so the text is less varied than real reports.
- Coordinates are random points around ward centres, not real addresses.
