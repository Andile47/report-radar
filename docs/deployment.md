# Deployment: the live dashboard

**Live site:** [reportradar.streamlit.app](https://reportradar.streamlit.app)

The dashboard runs on Streamlit Community Cloud, a free hosting service. It is built from the `main` branch of this repository, starting from `dashboard/app.py`, and installs the packages in `requirements.txt`.

## How an update reaches the live site

1. Push to `main` as usual.
2. Streamlit Cloud notices the push and rebuilds the app on its own, usually within a few minutes. Nobody needs to click anything.
3. Do the 2-minute check below.

If `requirements.txt` changed, the rebuild takes longer because the packages are reinstalled.

## What is different on the live site

The live site runs a fresh copy of the repository. It does **not** run `python run_all.py`, so anything kept out of git (see `.gitignore`) starts missing:

| Kept out of git | What the live site does instead |
| --- | --- |
| `workflow/data/tickets.csv` (tickets) | On the first visit, the 10 example reports in `workflow/inbox/new_reports_example.csv` are put through the real workflow, so the Workflow tab has tickets, approvals and emails. The tab says which tickets are examples. |
| `workflow/outbox/` (emails) | Filled by those example tickets. Emails are only saved, never sent: no mail server is set up. |
| `governance/logs/decisions.csv` (decision log) | The Risk & compliance tab shows `governance/logs/decisions_example.csv`, labelled as example decisions, until something has run. After the first visit to the Workflow tab, it shows the real log. |

Forecast, hotspot and classifier results are committed to git, so those tabs show the same figures as a local run.

**Anything saved on the live site is temporary.** Reports submitted and decisions made there are lost when the app restarts or rebuilds (after every push). On the next visit the 10 examples are loaded again. This is fine for a demo, and it means a real deployment would need a database.

## Before a demo

- **Wake the app 15 minutes before.** Streamlit Cloud puts an app to sleep after a period with no visitors. A sleeping app shows a "get this app back up" button and takes a minute or more to start.
- Don't push to `main` in the hour before a demo: every push rebuilds the app and clears any demo tickets you prepared.
- Keep the backup screenshots or recording (Role 5) ready offline in case the site or Wi-Fi fails.

## The 2-minute check after every push

1. Open the live site. It loads without a red error box.
2. Click through all 6 tabs: Overview, Forecast, Problem areas, Reports, Risk & compliance, Workflow.
3. Workflow: "My team's queue" shows tickets, "Waiting for approval" shows tickets with Approve, Reassign and Reject, and "Sent emails" lists emails.
4. Submit a short test report (for example "Pothole on 4th Avenue", Pan Africa) and check it gets a ticket number, a team and a fix date.
5. Risk & compliance: the risk register and the latest decisions are shown.

If a step fails, tell the team straight away, then check the app's logs (below).

## If something goes wrong

Whoever deployed the app manages it from [share.streamlit.io](https://share.streamlit.io) while signed in with their GitHub account. From the app's menu there:

- **Manage app** opens the logs, which show the error behind a red error box.
- **Reboot app** restarts it: use this if it is stuck. Saved tickets are cleared.
- **Settings** holds the Python version and secrets. No secrets are needed today; real email sending would need `SMTP_HOST`, `SMTP_USER` and `SMTP_PASSWORD` there.

Most failures after a push are a package missing from `requirements.txt` or a file the code expects that is kept out of git. Running `streamlit run dashboard/app.py` on a fresh clone usually shows the same error locally.

## Speed

Once the app is awake, a first visit takes about 1.3 seconds to build the page and later visits about 0.5 seconds, because data reads are cached (measured with Streamlit's test runner on 10 Nov 2026). Waking from sleep is the only slow part.
