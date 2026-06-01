import re
from typing import Any


KNOWN_ACTIONS = [
    "entered",
    "enter",
    "seen",
    "seeing",
    "saw",
    "walked",
    "moved",
    "move",
    "carrying",
    "hearing",
    "heard",
    "stated",
    "reported",
    "mentioned",
    "looked",
    "appeared",
    "left",
    "arrived",
    "called",
    "argued",
]

KNOWN_OBJECTS = [
    "black backpack",
    "backpack",
    "vehicle",
    "car",
    "phone",
    "bag",
    "rear counter",
    "counter",
    "rear exit",
    "exit",
]

KNOWN_LOCATIONS = [
    "downtown pharmacy",
    "pharmacy",
    "rear exit",
    "rear counter",
    "counter",
    "back area",
]


EXCLUDED_PEOPLE_TERMS = {
    "I",
    "He",
    "She",
    "They",
    "It",
    "The",
    "A",
    "An",
    "Witness",
    "PM",
    "AM",
}


def extract_timestamps(text: str) -> list[str]:
    time_pattern = r"\b(?:around|approximately|at)?\s*(\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)?)\b"
    matches = re.findall(time_pattern, text)
    return list(dict.fromkeys(match.strip().upper() for match in matches))


def extract_people(text: str) -> list[str]:
    candidates = re.findall(r"\b[A-Z][a-z]+\b", text)

    people = [
        candidate
        for candidate in candidates
        if candidate not in EXCLUDED_PEOPLE_TERMS
    ]

    return list(dict.fromkeys(people))


def term_exists(text: str, term: str) -> bool:
    pattern = rf"\b{re.escape(term.lower())}\b"
    return re.search(pattern, text.lower()) is not None


def extract_known_terms(text: str, known_terms: list[str]) -> list[str]:
    found = []

    for term in known_terms:
        if term_exists(text=text, term=term):
            found.append(term)

    return list(dict.fromkeys(found))


def remove_nested_terms(terms: list[str]) -> list[str]:
    cleaned = []

    for term in terms:
        is_nested = any(
            term != other_term and term in other_term
            for other_term in terms
        )

        if not is_nested:
            cleaned.append(term)

    return cleaned


def extract_actions(text: str) -> list[str]:
    return extract_known_terms(text, KNOWN_ACTIONS)


def extract_objects(text: str) -> list[str]:
    objects = extract_known_terms(text, KNOWN_OBJECTS)
    return remove_nested_terms(objects)


def extract_locations(text: str) -> list[str]:
    locations = extract_known_terms(text, KNOWN_LOCATIONS)
    return remove_nested_terms(locations)


def calculate_extraction_confidence(
    people: list[str],
    locations: list[str],
    timestamps: list[str],
    actions: list[str],
) -> int:
    score = 30

    if people:
        score += 20
    if locations:
        score += 20
    if timestamps:
        score += 20
    if actions:
        score += 10

    return min(score, 100)


def build_event_draft(
    evidence_id: int,
    text: str,
    people: list[str],
    locations: list[str],
    timestamps: list[str],
    actions: list[str],
    objects: list[str],
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "time": timestamps[0] if timestamps else None,
        "location": locations[0] if locations else None,
        "participants": people,
        "actions": actions,
        "objects": objects,
        "description": text,
        "confidence": calculate_extraction_confidence(
            people=people,
            locations=locations,
            timestamps=timestamps,
            actions=actions,
        ),
    }


def process_evidence_text(evidence_id: int, text: str) -> dict[str, Any]:
    people = extract_people(text)
    locations = extract_locations(text)
    timestamps = extract_timestamps(text)
    actions = extract_actions(text)
    objects = extract_objects(text)

    event_draft = build_event_draft(
        evidence_id=evidence_id,
        text=text,
        people=people,
        locations=locations,
        timestamps=timestamps,
        actions=actions,
        objects=objects,
    )

    return {
        "evidence_id": evidence_id,
        "entities": {
            "people": people,
            "locations": locations,
            "timestamps": timestamps,
            "actions": actions,
            "objects": objects,
        },
        "event_draft": event_draft,
    }