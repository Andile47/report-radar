"""Measure classifier accuracy across language and vulnerable-group examples."""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from intake.classifier import process_report  # noqa: E402

TEST_FILE = Path(__file__).resolve().parent / "bias_test_reports.csv"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "bias_results_before.csv"
RESULT_FIELDS = [
    "dimension",
    "segment",
    "reports",
    "category_accuracy",
    "urgency_accuracy",
    "urgency_within_1_accuracy",
]


def load_reports(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reports = list(csv.DictReader(source))
    required = {
        "id", "language", "description", "expected_category",
        "expected_urgency", "group",
    }
    if not reports or not required.issubset(reports[0]):
        raise ValueError(f"{path} must contain test rows and columns: {', '.join(sorted(required))}")
    return reports


def measure(reports: list[dict[str, str]]) -> list[dict[str, str | int]]:
    buckets: dict[tuple[str, str], list[tuple[bool, bool, bool]]] = defaultdict(list)
    for report in reports:
        prediction = process_report(report["description"])
        expected_urgency = int(report["expected_urgency"])
        category_correct = prediction["category"] == report["expected_category"]
        urgency_correct = prediction["urgency"] == expected_urgency
        within_one = abs(prediction["urgency"] - expected_urgency) <= 1
        if report["group"] == "language":
            buckets[("language", report["language"])].append(
                (category_correct, urgency_correct, within_one)
            )
        buckets[("group", report["group"])].append(
            (category_correct, urgency_correct, within_one)
        )

    results = []
    for (dimension, segment), scores in sorted(buckets.items()):
        count = len(scores)
        results.append({
            "dimension": dimension,
            "segment": segment,
            "reports": count,
            "category_accuracy": f"{sum(score[0] for score in scores) / count:.1%}",
            "urgency_accuracy": f"{sum(score[1] for score in scores) / count:.1%}",
            "urgency_within_1_accuracy": f"{sum(score[2] for score in scores) / count:.1%}",
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=TEST_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    results = measure(load_reports(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(results)

    widths = {field: max(len(field), *(len(str(row[field])) for row in results)) for field in RESULT_FIELDS}
    print(" | ".join(field.ljust(widths[field]) for field in RESULT_FIELDS))
    print("-+-".join("-" * widths[field] for field in RESULT_FIELDS))
    for row in results:
        print(" | ".join(str(row[field]).ljust(widths[field]) for field in RESULT_FIELDS))
    print(f"Saved results to {args.output}")


if __name__ == "__main__":
    main()