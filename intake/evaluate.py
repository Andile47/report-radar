"""Report Radar - test the intake classifier on 30 tricky reports (Role 4).

Run from the repo root:  python intake/evaluate.py

Runs every report in intake/test_reports.csv (vague wording, mixed
problems, typos, slang, isiZulu) through the keyword classifier and, if an
API key is set, the LLM classifier too. Counts how many each gets wrong and
writes:
  intake/test_results.csv   one row per test report with every prediction
  intake/test_summary.md    the counts, for the handover
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from classifier import process_report  # noqa: E402
from llm_classifier import classify_with_llm, llm_available  # noqa: E402

TESTS = HERE / "test_reports.csv"
RESULTS = HERE / "test_results.csv"
SUMMARY = HERE / "test_summary.md"


def score(tests: pd.DataFrame, prefix: str) -> dict:
    cat_wrong = int((tests[f"{prefix}_category"] != tests["expected_category"]).sum())
    gap = (tests[f"{prefix}_urgency"] - tests["expected_urgency"]).abs()
    return {"category_wrong": cat_wrong, "urgency_exact": int((gap == 0).sum()),
            "urgency_off_by_2_plus": int((gap >= 2).sum()), "total": len(tests)}


def main() -> None:
    tests = pd.read_csv(TESTS)
    keyword = [process_report(d) for d in tests["description"]]
    tests["keyword_category"] = [r["category"] for r in keyword]
    tests["keyword_urgency"] = [r["urgency"] for r in keyword]
    tests["keyword_reason"] = [r["reason"] for r in keyword]
    results = {"Keyword classifier": score(tests, "keyword")}

    if llm_available():
        llm = [classify_with_llm(d) for d in tests["description"]]
        tests["llm_category"] = [r["category"] for r in llm]
        tests["llm_urgency"] = [r["urgency"] for r in llm]
        tests["llm_reason"] = [r["reason"] for r in llm]
        tests["llm_source"] = [r["source"] for r in llm]
        results["LLM classifier"] = score(tests, "llm")
    tests.to_csv(RESULTS, index=False)

    lines = ["# Intake classifier: results on 30 tricky test reports", "",
             "| Version | Category wrong | Urgency exactly right | Urgency off by 2+ levels |",
             "| --- | --- | --- | --- |"]
    for name, r in results.items():
        lines.append(f"| {name} | {r['category_wrong']} / {r['total']} | "
                     f"{r['urgency_exact']} / {r['total']} | {r['urgency_off_by_2_plus']} / {r['total']} |")
    if "LLM classifier" not in results:
        lines += ["", "LLM classifier not run: set ANTHROPIC_API_KEY and `pip install anthropic`, "
                  "then run this script again to add its row."]
    wrong = tests[tests["keyword_category"] != tests["expected_category"]]
    lines += ["", "## Keyword classifier: wrong categories", "",
              "| Test | Report | Expected | Got | Why |", "| --- | --- | --- | --- | --- |"]
    for row in wrong.itertuples():
        lines.append(f"| {row.id} | {row.description} | {row.expected_category} | "
                     f"{row.keyword_category} | {row.keyword_reason.split(' | ')[0]} |")
    off = tests[(tests["keyword_urgency"] - tests["expected_urgency"]).abs() >= 2]
    lines += ["", "## Keyword classifier: urgency off by 2 or more", "",
              "| Test | Report | Expected | Got |", "| --- | --- | --- | --- |"]
    for row in off.itertuples():
        lines.append(f"| {row.id} | {row.description} | {row.expected_urgency} | {row.keyword_urgency} |")
    SUMMARY.write_text("\n".join(lines) + "\n")

    for name, r in results.items():
        print(f"{name}: {r['category_wrong']}/{r['total']} categories wrong, "
              f"{r['urgency_exact']}/{r['total']} urgency exact, "
              f"{r['urgency_off_by_2_plus']}/{r['total']} urgency off by 2+")
    print(f"Wrote {RESULTS.name} and {SUMMARY.name} in intake/")


if __name__ == "__main__":
    main()
