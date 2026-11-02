"""Apply a fluent speaker's translation review to the bias test set.

How to review (one person per language is enough):
  1. Open governance/translation_review.csv in Excel or Google Sheets.
  2. For each row in your language, fill in:
       reviewer        your name
       verdict         approved   (the current text is natural and correct)
                       corrected  (put your wording in corrected_text)
       corrected_text  only when verdict is "corrected"
     The precheck_note and suggested_text columns are hints from an AI pre-check,
     not a fluent speaker. Ignore them if they are wrong.
  3. Save as CSV, then run from the repo root:
       python governance/apply_translation_review.py
       python governance/bias_check.py
     The second command re-measures the classifier on the checked wording.

Reviewed rows lose their "CHECK-" prefix in governance/bias_test_reports.csv.
Rows without a reviewer and verdict are left as they are.
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REVIEW_FILE = HERE / "translation_review.csv"
TEST_FILE = HERE / "bias_test_reports.csv"
VERDICTS = {"approved", "corrected"}


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def apply_review(review_file=REVIEW_FILE, test_file=TEST_FILE):
    """Update the test set from the review sheet. Returns a summary dict."""
    reviews = {r["id"].strip(): r for r in read_csv(review_file)}
    tests = read_csv(test_file)
    summary = {"approved": [], "corrected": [], "pending": [], "problems": []}

    for test in tests:
        review = reviews.get(test["id"]) or reviews.get("CHECK-" + test["id"])
        if review is None:
            continue
        verdict = review.get("verdict", "").strip().lower()
        reviewer = review.get("reviewer", "").strip()
        corrected = review.get("corrected_text", "").strip()
        if not verdict:
            summary["pending"].append(test["id"])
            continue
        if verdict not in VERDICTS:
            summary["problems"].append(f"{test['id']}: verdict must be approved or corrected")
            continue
        if not reviewer:
            summary["problems"].append(f"{test['id']}: add the reviewer's name")
            continue
        if verdict == "corrected":
            if not corrected:
                summary["problems"].append(f"{test['id']}: corrected but corrected_text is empty")
                continue
            test["description"] = corrected
        summary[verdict].append(test["id"])
        test["id"] = test["id"].removeprefix("CHECK-")

    if summary["approved"] or summary["corrected"]:
        write_csv(test_file, tests, list(tests[0]))
    return summary


def main():
    summary = apply_review()
    print(f"Approved: {len(summary['approved'])}  Corrected: {len(summary['corrected'])}  "
          f"Still waiting: {len(summary['pending'])}")
    for problem in summary["problems"]:
        print(f"  Not applied - {problem}")
    if summary["approved"] or summary["corrected"]:
        print("Now re-run:  python governance/bias_check.py")
    return 1 if summary["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
