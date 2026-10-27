"""Tests for the intake classifiers. Run from the repo root:  pytest intake"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import classifier as c  # noqa: E402
import llm_classifier as llm  # noqa: E402


@pytest.mark.parametrize("text, category", [
    ("Burst pipe flooding 4th Avenue, water running down the road", "water"),
    ("Pothole filled with water after the rain, taxis swerving", "roads"),
    ("Blocked stormwater drain causing flooding at intersection", "roads"),
    ("Drain blocked, grey water pooling outside our house", "sanitation"),
    ("Streetlight on all day, wasting power", "streetlights"),
    ("Whole street dark since the storm", "streetlights"),
    ("Akukho ugesi since last night, 7th Avenue", "electricity"),
    ("Dead animal on the roadside near London Road", "refuse"),
])
def test_dataset_style_reports(text, category):
    assert c.classify_report(text) == category


def test_typos_are_fixed_but_real_words_are_not():
    assert c.normalise("no watr") == "no water"
    assert c.normalise("whole street") == "whole street"


def test_unclear_reports_go_to_review():
    assert c.process_report("Something is wrong please come")["review_required"]


def test_urgency_levels():
    assert c.score_urgency("Live wires hanging low across the road") == 5
    assert c.score_urgency("No water since this morning") == 3
    assert c.score_urgency("Small crack and sinking tar near the school gate") == 1
    assert c.score_urgency("Water outage affecting the whole block, clinic nearby has no water") == 5


def test_school_or_clinic_raises_urgency():
    assert c.score_urgency("Pothole near the clinic") == c.score_urgency("Pothole") + 1


def test_every_result_has_a_reason():
    result = c.process_report("Big pothole on 10th Avenue damaging cars")
    assert result["reason"].startswith("roads")


def test_llm_reply_is_parsed_and_checked():
    reply = 'Sure! {"category": "water", "urgency": 4, "reason": "no water"}'
    assert llm.parse_reply(reply) == {"category": "water", "urgency": 4, "reason": "no water"}
    with pytest.raises(ValueError):
        llm.parse_reply('{"category": "parking", "urgency": 3}')
    with pytest.raises(ValueError):
        llm.parse_reply('{"category": "water", "urgency": 9}')


def test_llm_classifier_uses_the_model_reply():
    fake = lambda prompt: '{"category": "roads", "urgency": 4, "reason": "robot out"}'  # noqa: E731
    result = llm.classify_with_llm("Robot not working", ask=fake)
    assert result == {"category": "roads", "urgency": 4, "reason": "robot out", "source": "llm"}


def test_llm_classifier_falls_back_to_keywords():
    def broken(prompt):
        raise ConnectionError("no network")
    result = llm.classify_with_llm("No water since this morning", ask=broken)
    assert result["source"] == "keywords"
    assert result["category"] == "water"


def test_prompt_contains_the_report_and_categories():
    prompt = llm.build_prompt("Amanzi awekho")
    assert "Amanzi awekho" in prompt and "streetlights" in prompt
