# Data Card: Report Radar

## What data we hold
`data/reports.csv`: 3,994 citizen service reports with report_id, timestamp, category, description (free text), ward_or_suburb, latitude, longitude, urgency (1-5), status and hours_to_resolve.

## Why we hold it
To classify reports by type and urgency, forecast workload and find problem areas, so a municipality can plan before surges arrive. Purpose: service delivery planning only.

## Where it comes from
Fully synthetic. Produced by our generator script. No real residents, addresses or personal details. A PII scan of all 3,994 descriptions found 0 phone numbers, ID numbers, emails, house numbers or names.

## Who can see it
Project team members through the GitHub repository and the dashboard. There is no access control on the dashboard yet.

## How long we keep it
The **decision log** keeps rows for 365 days; older rows are deleted automatically whenever it is written (change with `REPORT_RADAR_LOG_RETENTION_DAYS`). No retention rule is set yet for the **reports** themselves. A real deployment would need one (for example, delete or anonymise reports after a fixed period).

## Sensitive content
Some descriptions mention health or vulnerability (clinics, elderly or disabled residents). In real data this is special personal information under POPIA and needs stronger protection. Reports also carry exact latitude and longitude, which can identify a household.

## Protection built in
`governance/privacy.py` masks phone numbers, ID numbers, emails, house numbers and names before text is logged or sent to an outside LLM. It is pattern-based and will miss unusual formats, so a person must still review.

## Limits
Synthetic data shows that the method works, not what is true in Alexandra.
