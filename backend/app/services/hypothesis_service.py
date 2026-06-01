from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.hypothesis import HypothesisResult, HypothesisScenario
from app.services.contradiction_service import detect_case_contradictions
from app.services.timeline_service import reconstruct_case_timeline
from app.ai.llm_hypothesis_generator import generate_hypotheses_with_llm
from app.core.config import settings
from app.models.evidence import Evidence


def get_supporting_evidence_ids(events: list[Event]) -> list[int]:
    evidence_ids = [
        event.evidence_id
        for event in events
        if event.evidence_id is not None
    ]

    return list(dict.fromkeys(evidence_ids))


def build_primary_sequence_hypothesis(
    events: list[Event],
) -> HypothesisScenario | None:
    if not events:
        return None

    event_ids = [event.id for event in events]
    evidence_ids = get_supporting_evidence_ids(events)

    first_event = events[0]
    last_event = events[-1]

    return HypothesisScenario(
        scenario_id="scenario_a",
        title="Primary extracted timeline sequence",
        description=(
            f"The available evidence supports a sequence beginning around "
            f"{first_event.event_time or 'an unknown time'} and continuing until "
            f"{last_event.event_time or 'an unknown time'}. This scenario follows the extracted "
            "events directly without adding strong assumptions."
        ),
        confidence_score=82,
        supporting_event_ids=event_ids,
        supporting_evidence_ids=evidence_ids,
        assumptions=[
            "Extracted event timestamps are approximately correct.",
            "Witness/source statements are being interpreted consistently.",
        ],
        contradictions=[],
        missing_evidence=[
            "Additional independent sources would strengthen this sequence.",
        ],
        recommended_validation=[
            "Compare event order against original evidence files.",
            "Add CCTV, GPS, phone logs, or additional witness statements if available.",
        ],
    )


def build_gap_inference_hypothesis(
    events: list[Event],
    inferred_events_count: int,
) -> HypothesisScenario | None:
    if not events or inferred_events_count == 0:
        return None

    event_ids = [event.id for event in events]
    evidence_ids = get_supporting_evidence_ids(events)

    return HypothesisScenario(
        scenario_id="scenario_b",
        title="Undocumented transition during timeline gap",
        description=(
            "The timeline contains one or more gaps where an undocumented movement, "
            "interaction, or transition may have occurred. This scenario explains the sequence "
            "by assuming that at least one missing event happened between known events."
        ),
        confidence_score=64,
        supporting_event_ids=event_ids,
        supporting_evidence_ids=evidence_ids,
        assumptions=[
            "The gap represents missing evidence rather than a complete absence of activity.",
            "The same participant appearing across events suggests continuity.",
        ],
        contradictions=[],
        missing_evidence=[
            "No direct evidence currently confirms what happened inside the gap.",
            "No visual or sensor-based confirmation exists for the inferred transition.",
        ],
        recommended_validation=[
            "Search for evidence covering the missing time window.",
            "Validate the inferred transition using stronger source types such as CCTV, GPS, or access logs.",
        ],
    )


def build_contradiction_hypothesis(
    events: list[Event],
    contradiction_descriptions: list[str],
) -> HypothesisScenario | None:
    if not contradiction_descriptions:
        return None

    event_ids = [event.id for event in events]
    evidence_ids = get_supporting_evidence_ids(events)

    return HypothesisScenario(
        scenario_id="scenario_c",
        title="Timestamp or location inconsistency scenario",
        description=(
            "At least one contradiction or suspicious transition was detected. "
            "This scenario assumes that part of the timeline may contain a timestamp issue, "
            "location ambiguity, or conflicting source interpretation."
        ),
        confidence_score=58,
        supporting_event_ids=event_ids,
        supporting_evidence_ids=evidence_ids,
        assumptions=[
            "One or more event records may contain inaccurate or imprecise metadata.",
            "Different sources may describe locations at different levels of detail.",
        ],
        contradictions=contradiction_descriptions,
        missing_evidence=[
            "No decisive evidence currently resolves the contradiction.",
            "More precise timestamps or location data are needed.",
        ],
        recommended_validation=[
            "Review the original evidence behind the contradicted events.",
            "Check whether the location labels refer to nearby or overlapping areas.",
            "Confirm whether timestamps are exact or approximate.",
        ],
    )


def calculate_highest_confidence_scenario_id(
    scenarios: list[HypothesisScenario],
) -> str | None:
    if not scenarios:
        return None

    highest = max(scenarios, key=lambda scenario: scenario.confidence_score)
    return highest.scenario_id


def build_case_context_for_llm(
    db: Session,
    case_id: int,
    events: list[Event],
    reconstruction,
    contradiction_summary,
) -> dict:
    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.id.asc())
        .all()
    )

    return {
        "case_id": case_id,
        "timeline_summary": reconstruction.timeline_summary,
        "timeline_risk": reconstruction.risk_assessment.model_dump(),
        "events": [
            {
                "event_id": event.id,
                "evidence_id": event.evidence_id,
                "time": event.event_time,
                "location": event.location,
                "description": event.description,
                "participants": event.participants or [],
                "actions": event.actions or [],
                "objects": event.objects or [],
                "confidence_score": event.confidence_score,
                "source_type": event.source_type,
            }
            for event in events
        ],
        "evidence": [
            {
                "evidence_id": item.id,
                "title": item.title,
                "evidence_type": item.evidence_type,
                "source_name": item.source_name,
                "summary": item.summary,
                "confidence_score": item.confidence_score,
                "extraction_method": item.extraction_method,
                "uncertainty_notes": item.uncertainty_notes or [],
            }
            for item in evidence_items
        ],
        "contradictions": [
            {
                "contradiction_type": finding.contradiction_type,
                "severity": finding.severity,
                "description": finding.description,
                "explanation": finding.explanation,
                "confidence_score": finding.confidence_score,
                "involved_event_ids": finding.involved_event_ids,
                "involved_evidence_ids": finding.involved_evidence_ids,
            }
            for finding in contradiction_summary.findings
        ],
        "timeline_gaps": [
            gap.model_dump()
            for gap in reconstruction.gaps
        ],
        "inferred_events": [
            inferred.model_dump()
            for inferred in reconstruction.inferred_events
        ],
    }


def convert_llm_hypotheses_to_result(
    case_id: int,
    llm_result,
) -> HypothesisResult:
    scenarios = [
        HypothesisScenario(
            scenario_id=scenario.scenario_id,
            title=scenario.title,
            description=scenario.description,
            confidence_score=scenario.confidence_score,
            supporting_event_ids=scenario.supporting_event_ids,
            supporting_evidence_ids=scenario.supporting_evidence_ids,
            assumptions=scenario.assumptions,
            contradictions=scenario.contradictions,
            missing_evidence=scenario.missing_evidence,
            recommended_validation=scenario.recommended_validation,
        )
        for scenario in llm_result.scenarios
    ]

    return HypothesisResult(
        case_id=case_id,
        total_scenarios=len(scenarios),
        highest_confidence_scenario_id=calculate_highest_confidence_scenario_id(scenarios),
        generation_method="llm",
        scenarios=scenarios,
        uncertainty_notice=llm_result.uncertainty_notice,
        llm_error=None,
    )


def generate_rule_based_case_hypotheses(
    db: Session,
    case_id: int,
    reconstruction,
    contradiction_summary,
    sorted_events: list[Event],
) -> HypothesisResult:
    contradiction_descriptions = [
        finding.description
        for finding in contradiction_summary.findings
    ]

    scenarios: list[HypothesisScenario] = []

    primary_scenario = build_primary_sequence_hypothesis(sorted_events)
    if primary_scenario:
        scenarios.append(primary_scenario)

    gap_scenario = build_gap_inference_hypothesis(
        events=sorted_events,
        inferred_events_count=len(reconstruction.inferred_events),
    )
    if gap_scenario:
        scenarios.append(gap_scenario)

    contradiction_scenario = build_contradiction_hypothesis(
        events=sorted_events,
        contradiction_descriptions=contradiction_descriptions,
    )
    if contradiction_scenario:
        scenarios.append(contradiction_scenario)

    return HypothesisResult(
        case_id=case_id,
        total_scenarios=len(scenarios),
        highest_confidence_scenario_id=calculate_highest_confidence_scenario_id(scenarios),
        generation_method="rule_based",
        scenarios=scenarios,
        uncertainty_notice=(
            "These hypotheses are analytical possibilities generated from extracted events, "
            "timeline gaps, and contradiction findings. They are not final conclusions and require human validation."
        ),
        llm_error=None,
    )

def generate_case_hypotheses(
    db: Session,
    case_id: int,
) -> HypothesisResult:
    reconstruction = reconstruct_case_timeline(db=db, case_id=case_id)
    contradiction_summary = detect_case_contradictions(db=db, case_id=case_id)

    events = (
        db.query(Event)
        .filter(Event.case_id == case_id)
        .all()
    )

    sorted_events = sorted(
        events,
        key=lambda event: event.event_time or "",
    )

    if settings.USE_LLM_HYPOTHESES and settings.OPENAI_API_KEY:
        try:
            case_context = build_case_context_for_llm(
                db=db,
                case_id=case_id,
                events=sorted_events,
                reconstruction=reconstruction,
                contradiction_summary=contradiction_summary,
            )

            llm_result = generate_hypotheses_with_llm(case_context=case_context)

            return convert_llm_hypotheses_to_result(
                case_id=case_id,
                llm_result=llm_result,
            )
        except Exception as exc:
            fallback_result = generate_rule_based_case_hypotheses(
                db=db,
                case_id=case_id,
                reconstruction=reconstruction,
                contradiction_summary=contradiction_summary,
                sorted_events=sorted_events,
            )
            fallback_result.generation_method = "rule_based_fallback"
            fallback_result.llm_error = str(exc)
            return fallback_result

    fallback_result = generate_rule_based_case_hypotheses(
        db=db,
        case_id=case_id,
        reconstruction=reconstruction,
        contradiction_summary=contradiction_summary,
        sorted_events=sorted_events,
    )
    fallback_result.generation_method = "rule_based"
    return fallback_result