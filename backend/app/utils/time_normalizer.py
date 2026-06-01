import re
from datetime import datetime


TIME_PATTERNS = [
    r"\b\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)\b",
    r"\b\d{1,2}:\d{2}\b",
]


def extract_clean_time(time_text: str | None) -> str | None:
    if not time_text:
        return None

    cleaned = time_text.strip()

    for pattern in TIME_PATTERNS:
        match = re.search(pattern, cleaned)

        if match:
            return normalize_time_format(match.group(0))

    return cleaned


def normalize_time_format(time_text: str) -> str:
    cleaned = time_text.strip().upper().replace(" ", "")

    for time_format in ("%I:%M%p", "%H:%M"):
        try:
            parsed = datetime.strptime(cleaned, time_format)
            return parsed.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            continue

    return time_text.strip()