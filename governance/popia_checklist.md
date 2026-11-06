# POPIA Checklist: Report Radar

Status key: **Met**, **Partly met**, **Not met**. All data in this project is synthetic. These statuses describe what would be needed before real resident data is used.

| # | POPIA principle | What it means here | Status | Evidence / gap |
|---|---|---|---|---|
| 1 | Purpose specification | Reports are used only for service-delivery planning, and residents are told so | Partly met | Purpose is written in the data card. No notice to residents exists yet. |
| 2 | Minimum data (minimality) | Collect and keep only what is needed | Partly met | Fields are limited to what the forecast and map need. Exact latitude/longitude may be more precise than needed (see R3-03). |
| 3 | Limit on further use | Data is not reused for other purposes | Partly met | Purpose is stated, but there is no technical or written rule stopping reuse. |
| 4 | Security safeguards | Protect data from loss, leaks and unauthorised access | Partly met | Personal details are masked before logging and LLM use (`governance/privacy.py`, tested). All emails are masked too (`workflow/notify.py`, tested). The resident's address is never saved in the ticket, outbox or log. No dashboard access control or encryption. |
| 5 | Retention limit | Delete data when no longer needed | Partly met | Decision-log rows are deleted after 365 days (`governance/logger.py`, R4-04). No retention period is set yet for the reports themselves (R3-04). |
| 6 | Data quality | Data is complete, accurate and up to date | Partly met | A data check runs in `run_all.py`. Data is synthetic and household counts are placeholders (see R6-06). |
| 7 | Openness / transparency | People know what is collected and how decisions are made | Partly met | Decision log, transparency notes and model cards exist. Nothing is shown to residents. |
| 8 | Data subject participation | Residents can see and correct their reports | Not met | No process for access or correction requests (see R3-04). |
| 9 | Special personal information | Health and vulnerability details get stronger protection | Partly met | Risk identified (R3-03) and masking applied. No separate handling or restricted access yet. |
| 10 | Sending data to third parties | Outside companies handling data are controlled | Partly met | The LLM classifier is optional and is off by default. If used, text must be masked first. Emails are only saved as files unless SMTP_HOST, SMTP_USER and SMTP_PASSWORD are all set. If they are, the resident's address and the masked message pass through the mail provider. No agreement with the LLM or mail provider exists. |

## Summary
1 item not met, 9 partly met, 0 fully met. The main gaps are retention limits and the right of residents to see and correct their reports. Both must be fixed before any real data is used.
