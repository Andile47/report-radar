"""Checks that everyone's rows in governance/risk_register.csv follow the shared format.

If this test fails, read the message: it names the exact risk_id to fix.
Run with:  pytest governance
"""
from pathlib import Path

import pandas as pd

REGISTER = Path(__file__).resolve().parent / "risk_register.csv"
COLUMNS = ["risk_id", "risk", "area", "who_is_harmed", "likelihood", "impact",
           "score", "evidence", "mitigation", "owner", "status"]
STATUSES = {"open", "in progress", "mitigated", "closed"}


def load():
    assert REGISTER.exists(), "governance/risk_register.csv is missing"
    return pd.read_csv(REGISTER)


def test_header_is_the_shared_format():
    assert list(load().columns) == COLUMNS


def test_every_risk_has_a_unique_id():
    ids = load()["risk_id"].astype(str).str.strip()
    assert not (ids == "").any() and not ids.isin(["nan"]).any(), "a row has no risk_id"
    assert not ids.duplicated().any(), f"duplicate risk_id: {sorted(ids[ids.duplicated()])}"


def test_ratings_are_whole_numbers_from_1_to_5():
    df = load()
    for col in ("likelihood", "impact"):
        values = pd.to_numeric(df[col], errors="coerce")
        bad = df.loc[~values.between(1, 5) | (values % 1 != 0), "risk_id"].tolist()
        assert not bad, f"{col} must be 1 to 5 for: {bad}"


def test_score_is_likelihood_times_impact():
    df = load()
    wrong = df.loc[pd.to_numeric(df["score"], errors="coerce")
                   != pd.to_numeric(df["likelihood"]) * pd.to_numeric(df["impact"]), "risk_id"]
    assert wrong.empty, f"score is not likelihood x impact for: {wrong.tolist()}"


def test_owner_and_status_are_filled_in_properly():
    df = load()
    assert not df["owner"].isna().any(), "every risk needs an owner"
    status = df["status"].astype(str).str.strip().str.lower().str.replace("_", " ")
    bad = df.loc[~status.isin(STATUSES), "risk_id"].tolist()
    assert not bad, f"status must be Open, In progress, Mitigated or Closed for: {bad}"
