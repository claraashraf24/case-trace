from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session
from app.utils.time_normalizer import extract_clean_time
from app.models.event import Event
from app.schemas.timeline import (
    InferredTimelineEvent,
    TimelineConfidence,
    TimelineEvent,
    TimelineGap,
    TimelineReconstruction,
    TimelineReport,
    TimelineRiskAssessment,
)

def parse_event_time(time_text: str | None) -> datetime | None:
    if not time_text:
        return None

    clean_time = extract_clean_time(time_text)

    if not clean_time:
        return None

    cleaned = clean_time.strip().upper()

    for time_format in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(cleaned, time_format)
        except ValueError:
            continue

    return None


def event_sort_key(event: Event) -> tuple[int, datetime]:
    parsed_time = parse_event_time(event.event_time)

    if parsed_time is None:
        return (1, datetime.max)

    return (0, parsed_time)


def calculate_gap_minutes(
    first_time: str | None,
    second_time: str | None,
) -> int | None:
    first = parse_event_time(first_time)
    second = parse_event_time(second_time)

    if not first or not second:
        return None

    gap = second - first
    return int(gap.total_seconds() // 60)


def build_timeline_events(events: list[Event]) -> list[TimelineEvent]:
    return [
        TimelineEvent(
            event_id=event.id,
            evidence_id=event.evidence_id,
            event_time=event.event_time,
            location=event.location,
            description=event.description,
            participants=event.participants or [],
            actions=event.actions or [],
            objects=event.objects or [],
            confidence_score=event.confidence_score,
            source_type=event.source_type,
            status=event.status,
        )
        for event in events
    ]


def detect_timeline_gaps(events: list[Event]) -> list[TimelineGap]:
    gaps = []

    for index in range(len(events) - 1):
        current_event = events[index]
        next_event = events[index + 1]

        gap_minutes = calculate_gap_minutes(
            current_event.event_time,
            next_event.event_time,
        )

        if gap_minutes is None:
            gaps.append(
                TimelineGap(
                    from_event_id=current_event.id,
                    to_event_id=next_event.id,
                    from_time=current_event.event_time,
                    to_time=next_event.event_time,
                    gap_minutes=None,
                    message="Unable to calculate gap because one or both events have missing/invalid time.",
                )
            )
            continue

        if gap_minutes >= 5:
            gaps.append(
                TimelineGap(
                    from_event_id=current_event.id,
                    to_event_id=next_event.id,
                    from_time=current_event.event_time,
                    to_time=next_event.event_time,
                    gap_minutes=gap_minutes,
                    message=f"There is a {gap_minutes}-minute gap between these events. This may require more evidence.",
                )
            )

    return gaps

def infer_missing_events(
    events: list[Event],
    gaps: list[TimelineGap],
) -> list[InferredTimelineEvent]:
    inferred_events = []

    event_lookup = {event.id: event for event in events}

    for gap in gaps:
        if gap.gap_minutes is None:
            continue

        if gap.gap_minutes < 5:
            continue

        from_event = event_lookup.get(gap.from_event_id)
        to_event = event_lookup.get(gap.to_event_id)

        if not from_event or not to_event:
            continue

        shared_participants = list(
            set(from_event.participants or []) & set(to_event.participants or [])
        )

        from_location = from_event.location or "unknown location"
        to_location = to_event.location or "unknown location"

        if shared_participants:
            participant_text = ", ".join(shared_participants)
        else:
            participant_text = "one or more involved subjects"

        if from_location != to_location:
            inference_type = "possible_movement"
            description = (
                f"{participant_text} may have moved from {from_location} "
                f"toward {to_location} between {gap.from_time} and {gap.to_time}."
            )
            supporting_reason = (
                "The same participant appears in events before and after the gap, "
                "but the timeline does not contain a direct transition event."
            )
        else:
            inference_type = "possible_interaction_or_transition"
            description = (
                f"An undocumented action, interaction, or movement inside {from_location} "
                f"may have occurred between {gap.from_time} and {gap.to_time}."
            )
            supporting_reason = (
                "The timeline jumps forward while the participant remains connected "
                "to the same general location."
            )

        inferred_events.append(
            InferredTimelineEvent(
                inferred_time_window=f"{gap.from_time} - {gap.to_time}",
                between_event_ids=[gap.from_event_id, gap.to_event_id],
                inference_type=inference_type,
                description=description,
                supporting_reason=supporting_reason,
                confidence_score=55.0,
            )
        )

    return inferred_events


def calculate_timeline_confidence(events: list[Event]) -> TimelineConfidence:
    if not events:
        return TimelineConfidence(
            average_confidence=0,
            lowest_confidence=0,
            highest_confidence=0,
            total_events=0,
        )

    scores = [event.confidence_score for event in events]

    return TimelineConfidence(
        average_confidence=round(sum(scores) / len(scores), 2),
        lowest_confidence=min(scores),
        highest_confidence=max(scores),
        total_events=len(events),
    )

def assess_timeline_risk(
    events: list[Event],
    gaps: list[TimelineGap],
    inferred_events: list[InferredTimelineEvent],
    confidence: TimelineConfidence,
) -> TimelineRiskAssessment:
    review_flags = []
    quality_score = 100.0

    if not events:
        return TimelineRiskAssessment(
            timeline_risk_label="empty_timeline",
            timeline_quality_score=0,
            review_flags=["No extracted events are available for this case."],
        )

    if len(events) < 2:
        quality_score -= 25
        review_flags.append("Timeline has fewer than two events, making reconstruction weak.")

    if gaps:
        quality_score -= min(len(gaps) * 10, 30)
        review_flags.append("Timeline contains one or more time gaps.")

    if inferred_events:
        quality_score -= min(len(inferred_events) * 12, 36)
        review_flags.append("Timeline contains inferred missing events that require validation.")

    if confidence.average_confidence < 60:
        quality_score -= 25
        review_flags.append("Average event confidence is low.")

    if confidence.lowest_confidence < 50:
        quality_score -= 15
        review_flags.append("At least one event has very low confidence.")

    quality_score = max(round(quality_score, 2), 0)

    if quality_score >= 85 and not review_flags:
        risk_label = "high_confidence"
    elif quality_score >= 70:
        risk_label = "moderate_confidence"
    elif quality_score >= 45:
        risk_label = "needs_review"
    else:
        risk_label = "incomplete_or_low_confidence"

    return TimelineRiskAssessment(
        timeline_risk_label=risk_label,
        timeline_quality_score=quality_score,
        review_flags=review_flags,
    )


def build_timeline_summary(
    events: list[Event],
    gaps: list[TimelineGap],
    inferred_events: list[InferredTimelineEvent],
) -> str:
    if not events:
        return "No events have been extracted for this case yet."

    first_event = events[0]
    last_event = events[-1]

    summary = (
        f"Timeline reconstructed from {len(events)} extracted event(s), "
        f"starting at {first_event.event_time or 'unknown time'} "
        f"and ending at {last_event.event_time or 'unknown time'}."
    )

    if gaps:
        summary += f" {len(gaps)} timeline gap(s) were detected and should be reviewed."

    if inferred_events:
        summary += (
            f" {len(inferred_events)} possible missing event(s) were inferred "
            "from timeline gaps, but they require validation with more evidence."
        )

    return summary


def reconstruct_case_timeline(
    db: Session,
    case_id: int,
) -> TimelineReconstruction:
    events = (
        db.query(Event)
        .filter(Event.case_id == case_id)
        .all()
    )

    sorted_events = sorted(events, key=event_sort_key)

    timeline_events = build_timeline_events(sorted_events)
    gaps = detect_timeline_gaps(sorted_events)
    inferred_events = infer_missing_events(sorted_events, gaps)
    confidence = calculate_timeline_confidence(sorted_events)
    risk_assessment = assess_timeline_risk(
        events=sorted_events,
        gaps=gaps,
        inferred_events=inferred_events,
        confidence=confidence,
    )
    summary = build_timeline_summary(sorted_events, gaps, inferred_events)

    return TimelineReconstruction(
        case_id=case_id,
        total_events=len(sorted_events),
        timeline_summary=summary,
        events=timeline_events,
        gaps=gaps,
        inferred_events=inferred_events,
        confidence=confidence,
        risk_assessment=risk_assessment,
    )

def format_event_for_report(event: TimelineEvent) -> str:
    participants = ", ".join(event.participants or []) or "Unknown participant"
    actions = ", ".join(event.actions or []) or "unspecified action"
    location = event.location or "unknown location"
    event_time = event.event_time or "unknown time"

    return (
        f"At {event_time}, {participants} was associated with {actions} "
        f"at {location}. Confidence: {event.confidence_score}%."
    )


def build_recommended_next_steps(
    reconstruction: TimelineReconstruction,
) -> list[str]:
    recommendations = []

    if reconstruction.gaps:
        recommendations.append(
            "Review additional evidence sources for the detected timeline gaps."
        )

    if reconstruction.inferred_events:
        recommendations.append(
            "Validate inferred missing events using stronger evidence such as CCTV, GPS logs, or additional witness statements."
        )

    if reconstruction.risk_assessment.timeline_risk_label != "high_confidence":
        recommendations.append(
            "Treat the reconstructed timeline as analytical support, not a final conclusion."
        )

    if reconstruction.confidence.lowest_confidence < 70:
        recommendations.append(
            "Prioritize reviewing low-confidence events before relying on the timeline."
        )

    if not recommendations:
        recommendations.append(
            "Continue monitoring for new evidence that may strengthen or challenge the reconstructed sequence."
        )

    return recommendations


def build_timeline_report(
    db: Session,
    case_id: int,
) -> TimelineReport:
    reconstruction = reconstruct_case_timeline(db=db, case_id=case_id)

    key_events = [
        format_event_for_report(event)
        for event in reconstruction.events
    ]

    timeline_gaps = [
        gap.message
        for gap in reconstruction.gaps
    ]

    inferred_missing_events = [
        f"{item.description} Reason: {item.supporting_reason} Confidence: {item.confidence_score}%."
        for item in reconstruction.inferred_events
    ]

    return TimelineReport(
        case_id=case_id,
        report_title=f"Timeline Reconstruction Report — Case {case_id}",
        executive_summary=reconstruction.timeline_summary,
        key_events=key_events,
        timeline_gaps=timeline_gaps,
        inferred_missing_events=inferred_missing_events,
        risk_label=reconstruction.risk_assessment.timeline_risk_label,
        quality_score=reconstruction.risk_assessment.timeline_quality_score,
        recommended_next_steps=build_recommended_next_steps(reconstruction),
        uncertainty_notice=(
            "This report is generated from extracted and inferred evidence. "
            "It should support investigation and analysis, not replace human review or establish final truth."
        ),
    )