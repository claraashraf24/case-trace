def normalize_location_zone(location: str | None) -> str | None:
    if not location:
        return None

    text = location.lower().strip()

    pharmacy_keywords = [
        "pharmacy",
        "counter",
        "rear exit",
        "back area",
        "rear counter",
    ]

    outside_keywords = [
        "parking",
        "parking lot",
        "alley",
        "street",
        "vehicle",
        "car",
        "outside",
    ]

    if any(keyword in text for keyword in outside_keywords):
        return "outside_area"

    if any(keyword in text for keyword in pharmacy_keywords):
        return "pharmacy_area"

    return text