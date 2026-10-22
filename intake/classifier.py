
import re
import pandas as pd
from pathlib import Path



# 1. Keywords used to identify report categories
CATEGORY_KEYWORDS = {
    "water": [
        "water", "pipe burst", "water leak", "leaking pipe",
        "water outage", "tap", "standpipe", "no water"
    ],
    "electricity": [
        "electricity", "power outage", "load-shedding",
        "blackout", "electrical", "cable theft", "power line"
    ],
    "roads": [
        "pothole", "road", "pavement", "traffic light",
        "road damage", "sinkhole", "speed hump", "flooding road"
    ],
    "sanitation": [
        "sewage", "sewer", "manhole", "drain",
        "toilet", "wastewater", "overflowing sewage"
    ],
    "refuse": [
        "rubbish", "garbage", "refuse", "illegal dumping",
        "litter", "waste collection", "building rubble"
    ],
    "streetlights": [
        "streetlight", "street light", "street lights",
        "lamp post", "dark street", "broken light"
    ]
}


# 2. Classify a citizen's report
def classify_report(description):
    text = description.lower()
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(
            1 for keyword in keywords
            if re.search(
                r"\b" + re.escape(keyword) + r"\b",
                text
            )
        )

    best_category = max(scores, key=scores.get)

    # No matching keywords: send for manual review
    if scores[best_category] == 0:
        return "other"

    # Avoid arbitrary classification when categories tie
    highest_score = scores[best_category]
    tied_categories = [
        category for category, score in scores.items()
        if score == highest_score
    ]

    if len(tied_categories) > 1:
        return "other"

    return best_category


# 3. Assign urgency from 1 (low) to 5 (critical)
def score_urgency(description):
    text = description.lower()

    critical_keywords = [
        "life-threatening", "electrocut",
        "person trapped", "major burst pipe",
        "sinkhole", "road collapse",
        "flooding homes", "fire", "live wire"
    ]

    high_keywords = [
        "hospital", "clinic", "school",
        "whole block", "multiple streets",
        "sewage overflowing", "burst pipe",
        "flooding", "exposed cable"
    ]

    medium_keywords = [
        "leak", "outage", "not working",
        "broken", "overflow", "blocked",
        "no water", "cable theft"
    ]

    low_keywords = [
        "small crack", "minor", "cosmetic",
        "slightly damaged"
    ]

    if any(word in text for word in critical_keywords):
        return 5
    elif any(word in text for word in high_keywords):
        return 4
    elif any(word in text for word in medium_keywords):
        return 3
    elif any(word in text for word in low_keywords):
        return 1
    else:
        return 2


# 4. Process an incoming report
def process_report(description):
    category = classify_report(description)
    urgency = score_urgency(description)

    return {
        "description": description,
        "category": category,
        "urgency": urgency,
        "review_required": category == "other"
    }


def process_csv(input_file, output_file):
    df = pd.read_csv(input_file)

    if "description" not in df.columns:
        raise ValueError("CSV must contain a 'description' column.")

    results = df["description"].fillna("").apply(process_report)

    # Preserve the original category and urgency for comparison
    df["predicted_category"] = results.apply(
        lambda result: result["category"]
    )
    df["predicted_urgency"] = results.apply(
        lambda result: result["urgency"]
    )
    df["review_required"] = results.apply(
        lambda result: result["review_required"]
    )

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    print(f"Processed {len(df)} reports.")
    print(f"Saved results to {output_path}")
    print("\nPredicted categories:")
    print(df["predicted_category"].value_counts())
    print("\nUrgency distribution:")
    print(df["predicted_urgency"].value_counts().sort_index())


if __name__ == "__main__":
    process_csv(
        "data/reports_clean.csv",
        "data/reports_classified.csv"
    )
