import csv

from governance.apply_translation_review import apply_review

HEADER = "id,language,description,expected_category,expected_urgency,group\n"
REVIEW_HEADER = "id,language,english,current_text,precheck_note,suggested_text,reviewer,verdict,corrected_text\n"


def setup(tmp_path, review_rows):
    tests = tmp_path / "tests.csv"
    tests.write_text(HEADER + "L01-en,English,There is no water,water,3,language\n"
                     "CHECK-L01-af,Afrikaans,Daar is geen water nie,water,3,language\n"
                     "CHECK-L07-af,Afrikaans,Riool vloei,sanitation,5,language\n"
                     "CHECK-L01-zu,isiZulu,Awekho amanzi,water,3,language\n", encoding="utf-8")
    review = tmp_path / "review.csv"
    review.write_text(REVIEW_HEADER + "".join(review_rows), encoding="utf-8")
    return tests, review


def ids_and_text(path):
    return [(r["id"], r["description"]) for r in csv.DictReader(open(path, encoding="utf-8"))]


def test_approved_and_corrected_rows_lose_the_check_prefix(tmp_path):
    tests, review = setup(tmp_path, [
        "CHECK-L01-af,Afrikaans,,,,,Anna,approved,\n",
        "CHECK-L07-af,Afrikaans,,,,,Anna,Corrected,Die riool loop oor\n",
        "CHECK-L01-zu,isiZulu,,,,,,,\n",
    ])
    summary = apply_review(review, tests)
    assert summary["approved"] == ["CHECK-L01-af"] and summary["corrected"] == ["CHECK-L07-af"]
    assert summary["pending"] == ["CHECK-L01-zu"] and summary["problems"] == []
    assert ids_and_text(tests) == [
        ("L01-en", "There is no water"), ("L01-af", "Daar is geen water nie"),
        ("L07-af", "Die riool loop oor"), ("CHECK-L01-zu", "Awekho amanzi")]
    apply_review(review, tests)  # running again changes nothing
    assert ids_and_text(tests)[2] == ("L07-af", "Die riool loop oor")


def test_incomplete_reviews_are_not_applied(tmp_path):
    tests, review = setup(tmp_path, [
        "CHECK-L01-af,Afrikaans,,,,,,approved,\n",
        "CHECK-L07-af,Afrikaans,,,,,Anna,corrected,\n",
        "CHECK-L01-zu,isiZulu,,,,,Sipho,looks ok,\n",
    ])
    summary = apply_review(review, tests)
    assert len(summary["problems"]) == 3
    assert [i for i, _ in ids_and_text(tests)] == ["L01-en", "CHECK-L01-af", "CHECK-L07-af", "CHECK-L01-zu"]


def test_review_sheet_covers_every_unchecked_translation():
    from governance.apply_translation_review import REVIEW_FILE, TEST_FILE, read_csv
    unchecked = {r["id"] for r in read_csv(TEST_FILE) if r["id"].startswith("CHECK-")}
    assert unchecked <= {r["id"] for r in read_csv(REVIEW_FILE)}
