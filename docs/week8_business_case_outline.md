# Report Radar: Week 8 Business Case

**Audience:** Municipal executive or industry panel  
**Presenter:** Tshepo Tleane, Business Case Lead  
**Tagline:** Know where needs are rising.

> All findings and example reports in the project are synthetic. They demonstrate the approach, not actual municipal service performance. Do not use them to make decisions about real residents.

## Slide 1: Report Radar helps leaders see where needs are rising

- A service-report planning concept for Alexandra
- “Know where needs are rising.”
- Business Case Lead: Tshepo Tleane

**Visual:** Use Role 5's map-pin logo idea, brand colours, and a simple Alexandra map image.

**Speaker notes:**  
Good morning. We are presenting Report Radar, a project built around a practical municipal challenge: making service reports easier to sort, understand, and plan around. The name reflects its purpose: helping teams see where needs may be rising. Today, we will show what the project does, what its synthetic test data suggests, what still needs work, and what a carefully scoped pilot could examine.

**Source:** [Brand guide](brand.md)

## Slide 2: Every service report needs attention before it reaches the right team

- Residents report water, electricity, roads, sanitation, refuse, and streetlight problems.
- Reports need to be sorted, prioritised, and directed.
- Workload can rise after events such as storms or heatwaves.

**Visual:** A simple resident report branching into six service types.

**Speaker notes:**  
Residents can report many kinds of problems, from burst pipes to broken streetlights. Each report needs to be understood, prioritised, and sent to the appropriate service team. When many reports arrive close together, teams may have more work to organise. The project is designed to help with that coordination. We are not claiming measured municipal delays here; the project's current findings come from synthetic data.

**Source:** [One-page explanation](one_page_explanation.md)

## Slide 3: Report Radar connects reports to planning, with people involved where judgment matters

- Sorts report type and urgency
- Forecasts workload and maps report hotspots
- Sends urgent or unclear cases for human review

**Visual:** One clear flow: resident report -> sorting -> human review when needed -> team and deadline; beside it, forecast and hotspot views.

**Speaker notes:**  
The project brings several tasks into one view. It sorts a report by problem type and urgency, forecasts how many reports may arrive, and shows where reports cluster. Its workflow description also includes routing reports to teams and assigning deadlines. Urgent or unclear reports should receive supervisor review. The visuals we show today are based on synthetic examples, so they demonstrate the approach, not proven results in live municipal operations.

**Sources:** [One-page explanation](one_page_explanation.md), [Workflow model card](../governance/model_cards/workflow.md)

## Slide 4: The dashboard lets us inspect the sample results and their limits

- Show forecast, hotspot, and risk views
- Use synthetic examples only
- Do not present email as live: messages are saved, not sent

**Visual:** A short, prepared dashboard walkthrough at [reportradar.streamlit.app](https://reportradar.streamlit.app).

**Speaker notes:**  
I'll show the dashboard's forecast, hotspot, and risk views, using the project's synthetic data. As we look at each result, I'll point out what it can and cannot tell us. One important limit: the workflow documentation says messages are saved to an outbox and are not actually sent. We should demonstrate the report-to-ticket workflow only if that part has been checked and is working on the presentation day.

**Sources:** [Workflow model card](../governance/model_cards/workflow.md), [Week 7 user guide](week7_user_guide.md)
