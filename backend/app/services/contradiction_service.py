from datetime import datetime
from app.utils.location_normalizer import normalize_location_zone
from sqlalchemy.orm import Session
from app.utils.time_normalizer import extract_clean_time
from app.models.event import Event
from app.schemas.contradiction import (
    ContradictionFinding,
    ContradictionReport,
    ContradictionSummary,
)


SEVERITY_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


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


def minutes_between(first_time: str | None, second_time: str | None) -> int | None:
    first = parse_event_time(first_time)
    second = parse_event_time(second_time)

    if not first or not second:
        return None

    return abs(int((second - first).total_seconds() // 60))


def share_participant(first_event: Event, second_event: Event) -> bool:
    first_people = set(first_event.participants or [])
    second_people = set(second_event.participants or [])

    return bool(first_people & second_people)


def get_shared_participants(first_event: Event, second_event: Event) -> list[str]:
    first_people = set(first_event.participants or [])
    second_people = set(second_event.participants or [])

    return list(first_people & second_people)


def build_missing_metadata_findings(events: list[Event]) -> list[ContradictionFinding]:
    findings = []

    for event in events:
        missing_fields = []

        if not event.event_time:
            missing_fields.append("time")

        if not event.location:
            missing_fields.append("location")

        if not event.participants:
            missing_fields.append("participants")

        if missing_fields:
            findings.append(
                ContradictionFinding(
                    contradiction_type="missing_event_metadata",
                    severity="low",
                    involved_event_ids=[event.id],
                    involved_evidence_ids=[event.evidence_id] if event.evidence_id else [],
                    description=(
                        f"Event {event.id} is missing important metadata: "
                        f"{', '.join(missing_fields)}."
                    ),
                    explanation=(
                        "Incomplete event metadata makes timeline reconstruction less reliable "
                        "and may affect contradiction detection."
                    ),
                    confidence_score=90,
                    recommended_review_action=(
                        "Review the source evidence and manually complete the missing event fields if possible."
                    ),
                )
            )

    return findings


def build_location_conflict_findings(events: list[Event]) -> list[ContradictionFinding]:
    findings = []

    sorted_events = sorted(
        events,
        key=lambda event: parse_event_time(event.event_time) or datetime.max,
    )

    for index in range(len(sorted_events) - 1):
        current_event = sorted_events[index]
        next_event = sorted_events[index + 1]

        if not share_participant(current_event, next_event):
            continue

        if not current_event.location or not next_event.location:
            continue

        current_zone = normalize_location_zone(current_event.location)
        next_zone = normalize_location_zone(next_event.location)

        if current_zone == next_zone:
            continue

        gap = minutes_between(current_event.event_time, next_event.event_time)

        if gap is None:
            continue

        if gap <= 3:
            shared_people = get_shared_participants(current_event, next_event)

            findings.append(
                ContradictionFinding(
                    contradiction_type="suspicious_location_transition",
                    severity="medium",
                    involved_event_ids=[current_event.id, next_event.id],
                    involved_evidence_ids=[
                        evidence_id
                        for evidence_id in [current_event.evidence_id, next_event.evidence_id]
                        if evidence_id is not None
                    ],
                    description=(
                        f"{', '.join(shared_people)} appears to move between different location zones "
                        f"within {gap} minute(s)."
                    ),
                                        explanation=(
                        "The same participant is linked to different location zones in a very short time window. "
                        "This may indicate a timestamp issue, location ambiguity, or conflicting evidence."
                    ),
                    confidence_score=70,
                    recommended_review_action=(
                        "Check timestamps, location labels, and source evidence for both events."
                    ),
                )
            )

    return findings


def build_confidence_mismatch_findings(events: list[Event]) -> list[ContradictionFinding]:
    findings = []

    if len(events) < 2:
        return findings

    scores = [event.confidence_score for event in events]
    highest_score = max(scores)
    lowest_score = min(scores)

    if highest_score - lowest_score >= 40:
        low_confidence_events = [
            event for event in events if event.confidence_score == lowest_score
        ]

        findings.append(
            ContradictionFinding(
                contradiction_type="confidence_mismatch",
                severity="low",
                involved_event_ids=[event.id for event in low_confidence_events],
                involved_evidence_ids=[
                    event.evidence_id
                    for event in low_confidence_events
                    if event.evidence_id is not None
                ],
                description=(
                    f"Some events have much lower confidence than others "
                    f"({lowest_score}% vs {highest_score}%)."
                ),
                explanation=(
                    "Large confidence differences do not prove contradiction, but they indicate "
                    "that some timeline parts may need stronger validation."
                ),
                confidence_score=65,
                recommended_review_action=(
                    "Review low-confidence events and compare them against stronger sources."
                ),
            )
        )

    return findings


def get_highest_severity(findings: list[ContradictionFinding]) -> str | None:
    if not findings:
        return None

    return max(
        [finding.severity for finding in findings],
        key=lambda severity: SEVERITY_RANK.get(severity, 0),
    )


def detect_case_contradictions(
    db: Session,
    case_id: int,
) -> ContradictionSummary:
    events = (
        db.query(Event)
        .filter(Event.case_id == case_id)
        .all()
    )

    findings = []
    findings.extend(build_missing_metadata_findings(events))
    findings.extend(build_location_conflict_findings(events))
    findings.extend(build_confidence_mismatch_findings(events))

    highest_severity = get_highest_severity(findings)

    return ContradictionSummary(
        case_id=case_id,
        total_findings=len(findings),
        highest_severity=highest_severity,
        has_critical_contradictions=highest_severity == "critical",
        findings=findings,
    )

def build_contradiction_executive_summary(
    summary: ContradictionSummary,
) -> str:
    if summary.total_findings == 0:
        return (
            "No major contradictions were detected in the currently extracted event set. "
            "This does not prove the timeline is complete; it only means no rule-based conflicts "
            "were found with the available data."
        )

    return (
        f"{summary.total_findings} potential contradiction finding(s) were detected. "
        f"The highest severity level is {summary.highest_severity}. "
        "These findings should be reviewed against the original evidence before drawing conclusions."
    )


def format_contradiction_finding(finding: ContradictionFinding) -> str:
    event_ids = ", ".join(str(event_id) for event_id in finding.involved_event_ids)
    evidence_ids = ", ".join(str(evidence_id) for evidence_id in finding.involved_evidence_ids)

    if not evidence_ids:
        evidence_ids = "manual or unavailable evidence reference"

    return (
        f"[{finding.severity.upper()}] {finding.description} "
        f"Involved events: {event_ids}. Evidence references: {evidence_ids}. "
        f"Reason: {finding.explanation}"
    )


def build_contradiction_recommended_actions(
    summary: ContradictionSummary,
) -> list[str]:
    if summary.total_findings == 0:
        return [
            "Continue adding evidence sources to strengthen contradiction coverage.",
            "Review the reconstructed timeline manually before relying on the current sequence.",
            "Add stronger source types such as CCTV summaries, GPS logs, or call records when available.",
        ]

    actions = []

    for finding in summary.findings:
        if finding.recommended_review_action not in actions:
            actions.append(finding.recommended_review_action)

    if summary.highest_severity in {"high", "critical"}:
        actions.append(
            "Escalate high-severity contradictions for priority human review."
        )

    actions.append(
        "Compare contradiction findings against original evidence before making any final judgment."
    )

    return actions


def build_contradiction_report(
    db: Session,
    case_id: int,
) -> ContradictionReport:
    summary = detect_case_contradictions(db=db, case_id=case_id)

    key_findings = [
        format_contradiction_finding(finding)
        for finding in summary.findings
    ]

    if not key_findings:
        key_findings = [
            "No contradiction findings were detected by the current rule-based engine."
        ]

    risk_level = summary.highest_severity or "none_detected"

    return ContradictionReport(
        case_id=case_id,
        report_title=f"Contradiction Analysis Report — Case {case_id}",
        executive_summary=build_contradiction_executive_summary(summary),
        risk_level=risk_level,
        total_findings=summary.total_findings,
        key_findings=key_findings,
        recommended_actions=build_contradiction_recommended_actions(summary),
        uncertainty_notice=(
            "This contradiction report is generated from available extracted events. "
            "It highlights possible inconsistencies for review, but it does not prove intent, guilt, or final truth."
        ),
    )