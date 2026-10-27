"""Report Radar - intake classifier (Role 4: Intake and Urgency Lead).

Decides two things for every citizen report:
  * category: water, electricity, roads, sanitation, refuse, streetlights,
    or "other" when it can't tell (sent for a person to review)
  * urgency:  1 (cosmetic) to 5 (danger to life)

How it works, in simple terms:
  1. Clean the text: lower-case it and fix small typos by matching words
     to our keyword list ("pothoel" -> "pothole", "watr" -> "water").
  2. Category: every keyword has a weight. Strong, specific phrases such
     as "sewage" or "pothole" count 3; general words such as "road" or
     "water" count 1. The category with the most points wins. A tie, or
     two strong problems in one report, goes to "other" for review.
  3. Urgency: each danger phrase has a level ("live wire" = 5, "no water"
     = 3, "small crack" = 1). The highest level found is used, and it goes
     up by one when a school, clinic or children are involved.
  4. Every result comes with a short reason listing the words that decided it.

Run from the repo root:  python intake/classifier.py
Writes intake/data/reports_clean.csv and intake/data/reports_classified.csv.
"""
from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:  # Week 6 decision log; the classifier works the same without it
    from governance.logger import log_decisions, make_row
except ImportError:
    log_decisions = make_row = None
INPUT_FILE = ROOT / "data" / "reports.csv"
CLEAN_FILE = Path(__file__).resolve().parent / "data" / "reports_clean.csv"
OUTPUT_FILE = Path(__file__).resolve().parent / "data" / "reports_classified.csv"

CATEGORIES = ["water", "electricity", "roads", "sanitation", "refuse", "streetlights"]

# 1. Category keywords: phrase -> points. Strong phrases (3) are specific to
#    one service; weak words (1) appear in many kinds of report.
CATEGORY_KEYWORDS = {
    "water": {
        "burst pipe": 3, "pipe burst": 3, "no water": 3, "amanzi": 3, "standpipe": 3,
        "water pressure": 3, "meter box": 2, "taps": 2, "tap": 2, "brown water": 3,
        "dirty water": 3, "water outage": 3, "trickle": 2, "leak": 1, "leaking": 1,
        "water": 1, "pipe": 1,
    },
    "electricity": {
        "electricity": 3, "ugesi": 3, "power": 2, "load-shedding": 3, "loadshedding": 3,
        "transformer": 3, "live wire": 3, "live wires": 3, "wires": 2, "wire": 2,
        "sparking": 3, "sparks": 3, "illegal connections": 3, "tripping": 3,
        "flickering": 2, "appliances": 2, "prepaid": 3,
    },
    "roads": {
        "pothole": 3, "potholes": 3, "speed hump": 3, "tar": 2, "road surface": 3,
        "road collapsed": 3, "sinkhole": 3, "open manhole": 3,
        "manhole cover": 3, "stormwater drain": 3, "robot": 3, "traffic light": 3,
        "hole": 2, "road": 1, "intersection": 1, "taxis": 1,
    },
    "sanitation": {
        "sewage": 3, "sewer": 3, "toilet": 3, "toilets": 3, "grey water": 3,
        "drain blocked": 3, "drain": 1, "stinks": 1, "smell": 1,
    },
    "refuse": {
        "rubbish": 3, "refuse": 3, "dumping": 3, "illegal dumping": 3, "rubble": 3,
        "bins": 3, "bin": 2, "litter": 3, "dead animal": 3,
        "garbage": 3, "rats": 1, "not collected": 2,
    },
    "streetlights": {
        "streetlight": 3, "streetlights": 3, "street light": 3, "street lights": 3,
        "high mast": 3, "light pole": 3, "lamp": 3, "lamp post": 3, "cable theft": 3,
        "cables": 2, "pole without lights": 3, "dark": 2,
        "lights": 1,
    },
}

# Things that are not a complaint at all (e.g. thanks for a repair).
NOT_A_COMPLAINT = [r"\bthank(s| you)\b.*\b(fix|fixed|fixing|sorted|repaired)\b"]

# 2. Urgency phrases: phrase -> level. The highest level found wins.
URGENCY_PHRASES = {
    5: ["live wire", "live wires", "transformer exploded", "exploded", "fire", "electrocut",
        "road collapsed", "sinkhole", "open manhole", "someone could fall",
        "raw sewage", "sewage flowing", "burst pipe", "pipe burst", "whole block"],
    4: ["sparking", "illegal connections", "brown water", "dirty water", "can't drink",
        "sewage overflowing", "toilets overflowing", "flooding", "washed away",
        "about to fall", "muggings", "burning", "smoke", "traffic light", "robot"],
    3: ["no water", "amanzi", "ugesi", "power out", "not working", "dark",
        "unsafe", "cable theft", "cables", "pothole", "dead animal",
        "bad smell", "flooded", "blocked", "rats", "standpipe", "since yesterday",
        "since last night", "weeks"],
    2: ["low", "trickle", "leaking", "flickering", "tripping", "load-shedding",
        "speed hump", "dumping", "rubble", "not collected", "grey water", "broken"],
    1: ["small crack", "minor", "cosmetic", "on all day", "missed our street"],
}
VULNERABLE = ["school", "clinic", "hospital", "creche", "children", "kids"]
DEFAULT_URGENCY = 2

VOCABULARY = sorted({word for words in CATEGORY_KEYWORDS.values() for phrase in words
                     for word in phrase.split() if len(word) >= 4})


# ---------- step 1: clean the text ----------
def normalise(description: str) -> str:
    """Lower-case, tidy spaces, and fix small typos in keyword-like words."""
    text = re.sub(r"\s+", " ", str(description).lower()).strip()
    fixed = []
    for word in re.findall(r"[a-z'-]+|\S", text):
        if len(word) >= 4 and word not in VOCABULARY:
            # same first letter: real typos rarely change it ("whole" is not "hole")
            match = difflib.get_close_matches(word, VOCABULARY, n=1, cutoff=0.85)
            word = match[0] if match and match[0][0] == word[0] else word
        fixed.append(word)
    return " ".join(fixed)


def contains(text: str, phrase: str) -> bool:
    return re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", text) is not None


# ---------- step 2: category ----------
def category_scores(text: str) -> dict[str, list[str]]:
    """Matched keywords per category. A phrase inside a longer matched phrase
    is not counted twice ("burst pipe" doesn't also count "pipe")."""
    found = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        hits = [p for p in sorted(keywords, key=len, reverse=True) if contains(text, p)]
        hits = [p for p in hits if not any(p != q and p in q for q in hits)]
        if hits:
            found[category] = hits
    return found


def classify_report(description: str) -> str:
    return classify_with_reason(description)[0]


def classify_with_reason(description: str) -> tuple[str, str]:
    """Return (category, reason). 'other' means a person should review it."""
    text = normalise(description)
    if any(re.search(p, text) for p in NOT_A_COMPLAINT):
        return "other", "looks like a thank-you, not a complaint"
    hits = category_scores(text)
    if not hits:
        return "other", "no service keywords found"
    points = {c: sum(CATEGORY_KEYWORDS[c][p] for p in words) for c, words in hits.items()}
    ranked = sorted(points, key=points.get, reverse=True)
    best = ranked[0]
    if len(ranked) > 1:
        second = ranked[1]
        if points[second] == points[best]:
            return "other", f"tie between {best} and {second}"
        strong_best = max(CATEGORY_KEYWORDS[best][p] for p in hits[best]) >= 3
        strong_second = max(CATEGORY_KEYWORDS[second][p] for p in hits[second]) >= 3
        if strong_best and strong_second and " and " in text and points[second] >= 3:
            return "other", f"two problems reported ({best} and {second})"
    return best, f"{best}: " + ", ".join(hits[best])


# ---------- step 3: urgency ----------
def score_urgency(description: str) -> int:
    return urgency_with_reason(description)[0]


def urgency_with_reason(description: str) -> tuple[int, str]:
    text = normalise(description)
    if any(re.search(p, text) for p in NOT_A_COMPLAINT):
        return 1, "not a complaint"
    matched = {level: [p for p in phrases if contains(text, p)]
               for level, phrases in URGENCY_PHRASES.items()}
    serious = [lvl for lvl in (5, 4, 3, 2) if matched[lvl]]
    if matched[1] and not any(lvl >= 4 for lvl in serious):
        return 1, "minor: " + ", ".join(matched[1])
    if not serious:
        return DEFAULT_URGENCY, "no urgency words, default level"
    level = serious[0]
    reason = f"level {level}: " + ", ".join(matched[level])
    vulnerable = [w for w in VULNERABLE if contains(text, w)]
    if vulnerable and 3 <= level < 5:
        level += 1
        reason += f"; +1 near {vulnerable[0]}"
    return level, reason


# ---------- step 4: process reports ----------
def process_report(description: str) -> dict:
    category, category_reason = classify_with_reason(description)
    urgency, urgency_reason = urgency_with_reason(description)
    return {
        "description": description,
        "category": category,
        "urgency": urgency,
        "review_required": category == "other",
        "reason": f"{category_reason} | {urgency_reason}",
    }


def clean_reports(df: pd.DataFrame) -> pd.DataFrame:
    """Tidy the raw reports: trim spaces, drop empty descriptions and
    repeated report IDs."""
    df = df.copy()
    df["description"] = df["description"].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    before = len(df)
    df = df[df["description"].fillna("") != ""].drop_duplicates("report_id")
    removed = before - len(df)
    if removed:
        print(f"Removed {removed} empty or duplicate reports")
    return df


def process_csv(input_file: Path = INPUT_FILE, output_file: Path = OUTPUT_FILE,
                clean_file: Path = CLEAN_FILE) -> pd.DataFrame:
    df = pd.read_csv(input_file)
    if "description" not in df.columns:
        raise ValueError("CSV must contain a 'description' column.")
    df = clean_reports(df)
    Path(clean_file).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(clean_file, index=False)

    results = pd.DataFrame([process_report(d) for d in df["description"]], index=df.index)
    df["predicted_category"] = results["category"]
    df["predicted_urgency"] = results["urgency"]
    df["review_required"] = results["review_required"]
    df["reason"] = results["reason"]
    df.to_csv(output_file, index=False)
    logged = log_classifications(df)

    print(f"Processed {len(df):,} reports -> {Path(output_file).relative_to(ROOT)}")
    if logged:
        print(f"Logged {logged:,} decisions -> governance/logs/decisions.csv")
    print(f"Sent for review (category 'other'): {df['review_required'].mean():.1%}")
    if "category" in df.columns:
        agree = (df["predicted_category"] == df["category"]).mean()
        print(f"Category agrees with the dataset label: {agree:.1%}")
    if "urgency" in df.columns:
        gap = (df["predicted_urgency"] - df["urgency"]).abs()
        print(f"Urgency exact: {(gap == 0).mean():.1%}, within 1 level: {(gap <= 1).mean():.1%}")
    return df


def log_classifications(df: pd.DataFrame) -> int:
    """Write one decision-log row per classified report. Only reads df."""
    if log_decisions is None:
        return 0
    ids = df["report_id"] if "report_id" in df.columns else pd.Series(df.index, index=df.index)
    rows = [
        make_row(
            "classifier", report_id, description,
            f"category={category}; urgency={urgency}; needs_review={'yes' if review else 'no'}",
            reason,
        )
        for report_id, description, category, urgency, review, reason in zip(
            ids, df["description"], df["predicted_category"], df["predicted_urgency"],
            df["review_required"], df["reason"])
    ]
    return log_decisions(rows)


if __name__ == "__main__":
    process_csv()
