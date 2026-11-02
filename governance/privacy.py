import re

_STREET_WORDS = r"(?:Street|Road|Avenue|Drive|Lane|Crescent|Close)"

# Order matters: email and ID run before phone so they are not partly matched.
_RULES = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"\b\d{13}\b"), "[ID]"),
    (re.compile(r"(?:\+27|0027|\b0)[\s-]?\d{2}[\s-]?\d{3}[\s-]?\d{4}\b"), "[PHONE]"),
    # Replaces only the house number and keeps the street name, e.g. "[HOUSE_NO] Jukskei Street"
    (re.compile(r"\b\d{1,4}(?=\s+(?:[A-Z][a-z]+\s+)+" + _STREET_WORDS + r"\b)"), "[HOUSE_NO]"),
    # House numbers written without a street name, e.g. "house 23", "no. 14", "stand 512"
    (re.compile(r"((?i:\b(?:house|stand|erf|unit|flat)\s+(?:no\.?\s*|number\s+)?|\bno\.\s*|#\s*))\d{1,5}[A-Za-z]?\b"),
     r"\1[HOUSE_NO]"),
    (re.compile(r"\b(?:Mr|Mrs|Ms|Mama|Gogo|Mkhulu|Sis|Bra)\.?\s+[A-Z][a-z]+\b"), "[NAME]"),
    (re.compile(r"((?i:my name is|called)\s+)[A-Z][a-z]+"), r"\1[NAME]"),
]


def mask_personal_info(text):
    """Replace phone numbers, ID numbers, emails, house numbers and names with placeholders."""
    if not isinstance(text, str):
        return text
    for pattern, placeholder in _RULES:
        text = pattern.sub(placeholder, text)
    return text
