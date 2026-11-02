import re
import pandas as pd

df = pd.read_csv("data/reports.csv")

patterns = {
    "phone": r"(?:\+27|\b0)[\s-]?\d{2}[\s-]?\d{3}[\s-]?\d{4}\b",
    "id_number": r"\b\d{13}\b",
    "email": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "house_number": r"\b\d{1,4}\s+[A-Z][a-z]+\s+(?:Street|Road|Avenue|Drive|Lane|Crescent|Close)\b",
    "name": r"\b(?:Mr|Mrs|Ms|Mama|Gogo|Mkhulu|Sis|Bra)\.?\s+[A-Z][a-z]+\b|\b(?:my name is|called)\s+[A-Z][a-z]+\b",
}

print(f"Total reports: {len(df)}\n")
for label, pattern in patterns.items():
    hits = df[df["description"].astype(str).str.contains(pattern, regex=True)]
    print(f"{label}: {len(hits)} reports")
    for text in hits["description"].head(3):
        print(f"   e.g. {text}")
