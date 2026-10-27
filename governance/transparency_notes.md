# How this was decided: transparency notes

Short notes for each dashboard tab, written for managers without a technical background. Each says what the system does, how sure it is, and what it can't do. The Risk & Compliance tab shows these notes; each one can also sit under its own tab.

## Overview

**How this was decided:** the summary combines the forecast, the problem areas and the sorted reports below it, using a year of synthetic reports from Alexandra. The numbers are good for planning, not exact: next week's figure is usually within about 4 reports of what really happens. A quiet area or a low number doesn't always mean fewer problems; some communities report less.

## Forecast

**How this was decided:** we counted reports per week for the past year, tested four simple methods on recent weeks, and used the most accurate one, the average of the last 4 weeks. It is usually within about 4 reports a week of what really happened, so read every number with its likely range. It can't see one-off events coming, such as storms or a summer water crisis, because it has only one year of history to learn from.

## Problem areas

**How this was decided:** reports were grouped into 5 areas by where they were made; 5 groups fitted the data best. The ranking shows where most reports come from, not where most problems are: an area may report less because of language, airtime or trust. Sending crews only to the busiest areas can make quiet areas wait longer. Urgent reports already wait a median of 44 hours in Tsutsumani, against 24 in Old Alexandra.

## Reports

**How this was decided:** each report's problem type and urgency (1 to 5) are chosen automatically from the words the resident used, and the "Why" column shows those words. It works well on common wording, but it got 4 of 30 deliberately tricky reports wrong. It understands only English and a few isiZulu phrases, so reports in other languages may be marked unclear or given low urgency. Treat the urgency as a first sort, and check anything that looks wrong; reports it can't sort are marked for a person to check.

## Every decision is recorded

Each sorted report and each forecast run is written to a decision log (`governance/logs/decisions.csv`): what was decided, when, why, and with which version of the rules. Personal details such as phone and ID numbers are hidden before anything is written. This lets anyone check or challenge a decision later.
