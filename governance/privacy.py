import re

_STREET_WORDS = r"(?:Street|Road|Avenue|Drive|Lane|Crescent|Close)"

# SA ID number: 13 digits, also written in groups, e.g. "900101 5009 087" or "900101-5009-087"
ID_PATTERN = r"\b\d{6}[\s-]?\d{4}[\s-]?\d{3}\b"
# SA phone number: 0 or +27/0027, an area or network code (optionally in brackets, e.g. "(082)"
# or "+27 (0)82"), then 7 digits in any grouping, e.g. "123 4567", "1234 567" or "1234567"
PHONE_PATTERN = r"(?:(?:\+|\b00)27[\s-]?(?:\(0\))?\(?|\(0|\b0)\d{2}\)?[\s-]?\d(?:[\s-]?\d){6}\b"

# Order matters: email and ID run before phone so they are not partly matched.
_RULES = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(ID_PATTERN), "[ID]"),
    (re.compile(PHONE_PATTERN), "[PHONE]"),
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
