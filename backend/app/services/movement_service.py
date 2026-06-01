from datetime import datetime

from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.movement import (
    MovementPoint,
    MovementReconstructionResponse,
    MovementSegment,
)
from app.utils.location_normalizer import normalize_location_zone
from app.utils.time_normalizer import extract_clean_time


LOCATION_COORDINATES = {
    "pharmacy_area": {
        "x": 50,
        "y": 45,
        "label": "Pharmacy Interior",
    },
    "rear_exit": {
        "x": 72,
        "y": 42,
        "label": "Rear Exit",
    },
    "counter_area": {
        "x": 42,
        "y": 48,
        "label": "Counter Area",
    },
    "outside_area": {
        "x": 86,
        "y": 70,
        "label": "Parking Lot / Outside",
    },
    "unknown": {
        "x": 50,
        "y": 80,
        "label": "Unknown Location",
    },
}


def classify_scene_location(location: str | None) -> str:
    if not location:
        return "unknown"

    text = location.lower()

    if "parking" in text or "outside" in text or "vehicle" in text or "alley" in text:
        return "outside_area"

    if "rear exit" in text:
        return "rear_exit"

    if "counter" in text:
        return "counter_area"

    if "pharmacy" in text or "back area" in text:
        return "pharmacy_area"

    return normalize_location_zone(location) or "unknown"


def parse_time_minutes(time_text: str | None) -> int | None:
    clean_time = extract_clean_time(time_text)

    if not clean_time:
        return None

    for time_format in ("%I:%M %p", "%H:%M"):
        try:
            parsed = datetime.strptime(clean_time, time_format)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue

    return None


def sort_events_by_time(events: list[Event]) -> list[Event]:
    return sorted(
        events,
        key=lambda event: parse_time_minutes(event.event_time) or 999999,
    )


def build_movement_point(event: Event) -> MovementPoint:
    scene_location = classify_scene_location(event.location)
    coordinates = LOCATION_COORDINATES.get(
        scene_location,
        LOCATION_COORDINATES["unknown"],
    )

    return MovementPoint(
        event_id=event.id,
        evidence_id=event.evidence_id,
        event_time=event.event_time,
        label=coordinates["label"],
        location=event.location,
        zone=scene_location,
        x=coordinates["x"],
        y=coordinates["y"],
        confidence_score=event.confidence_score,
        source_type=event.source_type,
        description=event.description,
    )


def build_movement_segment(
    current_event: Event,
    next_event: Event,
) -> MovementSegment:
    current_minutes = parse_time_minutes(current_event.event_time)
    next_minutes = parse_time_minutes(next_event.event_time)

    time_gap = None
    if current_minutes is not None and next_minutes is not None:
        time_gap = next_minutes - current_minutes

    current_zone = classify_scene_location(current_event.location)
    next_zone = classify_scene_location(next_event.location)

    is_suspicious = False
    alert = None

    if (
        current_zone != next_zone
        and current_zone != "unknown"
        and next_zone != "unknown"
        and time_gap is not None
        and time_gap <= 1
    ):
        is_suspicious = True
        alert = (
            "Rapid movement between different location zones. "
            "Review timestamp accuracy and location labels."
        )

    distance_label = (
        "same zone"
        if current_zone == next_zone
        else f"{current_zone} -> {next_zone}"
    )

    return MovementSegment(
        from_event_id=current_event.id,
        to_event_id=next_event.id,
        from_time=current_event.event_time,
        to_time=next_event.event_time,
        from_location=current_event.location,
        to_location=next_event.location,
        distance_label=distance_label,
        time_gap_minutes=time_gap,
        is_suspicious=is_suspicious,
        alert=alert,
    )


def reconstruct_case_movement(
    db: Session,
    case_id: int,
) -> MovementReconstructionResponse:
    events = (
        db.query(Event)
        .filter(Event.case_id == case_id)
        .all()
    )

    sorted_events = sort_events_by_time(events)

    points = [
        build_movement_point(event)
        for event in sorted_events
    ]

    segments = [
        build_movement_segment(sorted_events[index], sorted_events[index + 1])
        for index in range(len(sorted_events) - 1)
    ]

    suspicious_count = len([
        segment
        for segment in segments
        if segment.is_suspicious
    ])

    summary = (
        f"Movement reconstructed from {len(points)} timeline point(s). "
        f"{suspicious_count} suspicious transition(s) require review."
    )

    return MovementReconstructionResponse(
        case_id=case_id,
        total_points=len(points),
        total_segments=len(segments),
        points=points,
        segments=segments,
        summary=summary,
    )