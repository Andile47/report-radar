"""Report Radar - LLM version of the intake classifier (Role 4).

The same job as classifier.py, done by a large language model instead of
keywords. The model reads the report and returns JSON with a category,
an urgency from 1 to 5 and a one-line reason.

Use it from Python:

    from llm_classifier import classify_with_llm
    classify_with_llm("Burst pipe on 5th Avenue, water everywhere")
    # {'category': 'water', 'urgency': 5, 'reason': '...', 'source': 'llm'}

By default it calls Claude through the Anthropic API, which needs:
    pip install anthropic
    export ANTHROPIC_API_KEY=...        (Windows: set ANTHROPIC_API_KEY=...)
    export LLM_MODEL=claude-haiku-5-5   (optional, this is the default)

To use another LLM, pass your own `ask` function that takes the prompt text
and returns the model's reply text.

If the model is unavailable or replies with something that isn't valid
JSON, the report falls back to the keyword classifier, so intake never
stops working. The result's "source" says which one was used.
"""
from __future__ import annotations

import json
import os
import re
from typing import Callable

from classifier import CATEGORIES, process_report

PROMPT = """You sort citizen reports for a South African municipality (Alexandra, Johannesburg).

Read the report and reply with JSON only, no other text:
{{"category": "...", "urgency": N, "reason": "..."}}

category: one of {categories}, or "other" if it is not a service problem,
is too vague to tell, or describes two different problems.
urgency, from 1 to 5:
  1 = cosmetic or not a complaint
  2 = low: an inconvenience, no risk
  3 = medium: a service is not working (no water, no power, dark street)
  4 = high: a health or safety risk, or many people affected
  5 = critical: danger to life (live wires, open manholes, collapsed roads, raw sewage, fire)
Add one level if a school, clinic, creche or children are directly affected.
reason: one short sentence saying why.

Reports may contain typos, slang ("robot" = traffic light) or isiZulu
("amanzi awekho" = there is no water, "akukho ugesi" = there is no electricity).

Report: \"\"\"{description}\"\"\"
"""


def build_prompt(description: str) -> str:
    return PROMPT.format(categories=", ".join(CATEGORIES), description=description)


def parse_reply(reply: str) -> dict:
    """Pull the JSON object out of the model's reply and check it.
    Raises ValueError if the reply can't be trusted."""
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        raise ValueError("no JSON object in reply")
    data = json.loads(match.group(0))
    category = str(data.get("category", "")).strip().lower()
    if category not in CATEGORIES + ["other"]:
        raise ValueError(f"unknown category {category!r}")
    urgency = int(data.get("urgency"))
    if not 1 <= urgency <= 5:
        raise ValueError(f"urgency {urgency} outside 1-5")
    return {"category": category, "urgency": urgency,
            "reason": str(data.get("reason", "")).strip()}


def anthropic_ask(prompt: str) -> str:
    """Send the prompt to Claude and return the reply text."""
    import anthropic  # imported here so the rest works without the package

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=os.environ.get("LLM_MODEL", "claude-haiku-5-5"),
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def llm_available() -> bool:
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def classify_with_llm(description: str, ask: Callable[[str], str] | None = None) -> dict:
    """Classify one report with an LLM, falling back to keywords on any error."""
    ask = ask or anthropic_ask
    try:
        result = parse_reply(ask(build_prompt(description)))
        result["source"] = "llm"
    except Exception as error:  # network, key, bad JSON: never block intake
        fallback = process_report(description)
        result = {"category": fallback["category"], "urgency": fallback["urgency"],
                  "reason": f"keyword fallback ({type(error).__name__}): {fallback['reason']}",
                  "source": "keywords"}
    return result
