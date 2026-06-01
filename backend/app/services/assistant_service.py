from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.schemas.assistant import AssistantAnswer
from app.services.contradiction_service import detect_case_contradictions
from app.services.hypothesis_service import generate_case_hypotheses
from app.services.timeline_service import reconstruct_case_timeline
from app.ai.llm_investigation_assistant import answer_question_with_llm
from app.core.config import settings
from app.services.hypothesis_service import generate_case_hypotheses


def get_case_evidence_references(db: Session, case_id: int) -> list[str]:
    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.id.asc())
        .all()
    )

    return [
        f"Evidence #{item.id}: {item.title} ({item.source_name or 'Unknown source'})"
        for item in evidence_items
    ]


def answer_timeline_question(db: Session, case_id: int, question: str) -> AssistantAnswer:
    timeline = reconstruct_case_timeline(db=db, case_id=case_id)
    evidence_refs = get_case_evidence_references(db=db, case_id=case_id)

    event_lines = [
        f"{event.event_time or 'Unknown time'}: {event.description}"
        for event in timeline.events
    ]

    if timeline.gaps:
        gap_text = " Timeline gaps were detected and should be reviewed."
    else:
        gap_text = " No timeline gaps are currently detected."

    answer = (
        f"The reconstructed timeline contains {timeline.total_events} event(s). "
        + " ".join(event_lines)
        + gap_text
    )

    return AssistantAnswer(
        case_id=case_id,
        question=question,
        answer=answer,
        confidence_score=timeline.confidence.average_confidence,
        evidence_references=evidence_refs,
        limitations=[
            "This answer is based on extracted events and does not establish final truth.",
            "Approximate witness times may still require manual validation.",
        ],
        suggested_follow_up_questions=[
            "Which event has the lowest confidence?",
            "Are there any contradictions in this case?",
            "Which evidence supports the timeline?",
        ],
    )


def answer_contradiction_question(db: Session, case_id: int, question: str) -> AssistantAnswer:
    contradiction_summary = detect_case_contradictions(db=db, case_id=case_id)
    evidence_refs = get_case_evidence_references(db=db, case_id=case_id)

    if contradiction_summary.total_findings == 0:
        answer = (
            "No major contradictions were detected by the current rule-based engine. "
            "This does not prove the case is complete; it only means no contradictions were found "
            "using the currently extracted events."
        )
        confidence = 75.0
    else:
        finding_lines = [
            f"{finding.severity.upper()}: {finding.description} Recommended review: {finding.recommended_review_action}"
            for finding in contradiction_summary.findings
        ]

        answer = (
            f"{contradiction_summary.total_findings} possible contradiction finding(s) were detected. "
            + " ".join(finding_lines)
        )
        confidence = max(
            finding.confidence_score for finding in contradiction_summary.findings
        )

    return AssistantAnswer(
        case_id=case_id,
        question=question,
        answer=answer,
        confidence_score=confidence,
        evidence_references=evidence_refs,
        limitations=[
            "Contradiction findings are analytical flags, not final conclusions.",
            "The original evidence should be reviewed before making decisions.",
        ],
        suggested_follow_up_questions=[
            "Which events are involved in the contradiction?",
            "What evidence should be checked next?",
            "Could this contradiction be caused by approximate timestamps?",
        ],
    )


def answer_hypothesis_question(db: Session, case_id: int, question: str) -> AssistantAnswer:
    hypotheses = generate_case_hypotheses(db=db, case_id=case_id)
    evidence_refs = get_case_evidence_references(db=db, case_id=case_id)

    if not hypotheses.scenarios:
        answer = "No hypotheses were generated because there are not enough extracted events yet."
        confidence = 0.0
    else:
        scenario_lines = [
            (
                f"{scenario.title} ({scenario.confidence_score}%): "
                f"{scenario.description}"
            )
            for scenario in hypotheses.scenarios
        ]

        answer = (
            f"The system generated {hypotheses.total_scenarios} possible scenario(s). "
            + " ".join(scenario_lines)
        )

        confidence = max(scenario.confidence_score for scenario in hypotheses.scenarios)

    return AssistantAnswer(
        case_id=case_id,
        question=question,
        answer=answer,
        confidence_score=confidence,
        evidence_references=evidence_refs,
        limitations=[
            "Hypotheses are possible interpretations, not final conclusions.",
            "More evidence may change the generated scenarios.",
        ],
        suggested_follow_up_questions=[
            "Which hypothesis has the highest confidence?",
            "What evidence supports the top hypothesis?",
            "What evidence is still missing?",
        ],
    )


def answer_evidence_question(db: Session, case_id: int, question: str) -> AssistantAnswer:
    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.id.asc())
        .all()
    )

    evidence_refs = get_case_evidence_references(db=db, case_id=case_id)

    processed_count = len([item for item in evidence_items if item.status == "processed"])

    evidence_lines = [
        (
            f"Evidence #{item.id}: {item.title}, type: {item.evidence_type}, "
            f"source: {item.source_name or 'Unknown'}, status: {item.status}."
        )
        for item in evidence_items
    ]

    answer = (
        f"This case has {len(evidence_items)} evidence item(s), "
        f"with {processed_count} processed. "
        + " ".join(evidence_lines)
    )

    return AssistantAnswer(
        case_id=case_id,
        question=question,
        answer=answer,
        confidence_score=90.0,
        evidence_references=evidence_refs,
        limitations=[
            "Evidence quality depends on the uploaded source text.",
            "The assistant does not verify whether uploaded evidence is authentic.",
        ],
        suggested_follow_up_questions=[
            "Which evidence has been processed?",
            "Which evidence supports Event 2?",
            "What evidence should be added next?",
        ],
    )


def answer_general_case_question(db: Session, case_id: int, question: str) -> AssistantAnswer:
    timeline = reconstruct_case_timeline(db=db, case_id=case_id)
    contradictions = detect_case_contradictions(db=db, case_id=case_id)
    hypotheses = generate_case_hypotheses(db=db, case_id=case_id)
    evidence_refs = get_case_evidence_references(db=db, case_id=case_id)

    answer = (
        f"Case {case_id} currently has {timeline.total_events} reconstructed event(s), "
        f"{len(timeline.gaps)} timeline gap(s), "
        f"{contradictions.total_findings} contradiction finding(s), and "
        f"{hypotheses.total_scenarios} generated hypothesis scenario(s). "
        f"Timeline risk label: {timeline.risk_assessment.timeline_risk_label}."
    )

    return AssistantAnswer(
        case_id=case_id,
        question=question,
        answer=answer,
        confidence_score=80.0,
        evidence_references=evidence_refs,
        limitations=[
            "This is a high-level summary based on current extracted data.",
            "Adding new evidence may change the timeline, contradictions, and hypotheses.",
        ],
        suggested_follow_up_questions=[
            "What happened in the timeline?",
            "Are there contradictions?",
            "What are the generated hypotheses?",
        ],
    )



def build_case_context_for_assistant(db: Session, case_id: int) -> dict:
    timeline = reconstruct_case_timeline(db=db, case_id=case_id)
    contradictions = detect_case_contradictions(db=db, case_id=case_id)
    hypotheses = generate_case_hypotheses(db=db, case_id=case_id)

    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.id.asc())
        .all()
    )

    return {
        "case_id": case_id,
        "timeline": {
            "summary": timeline.timeline_summary,
            "risk_assessment": timeline.risk_assessment.model_dump(),
            "confidence": timeline.confidence.model_dump(),
            "events": [
                {
                    "event_id": event.event_id,
                    "evidence_id": event.evidence_id,
                    "time": event.event_time,
                    "location": event.location,
                    "description": event.description,
                    "participants": event.participants or [],
                    "actions": event.actions or [],
                    "objects": event.objects or [],
                    "confidence_score": event.confidence_score,
                    "source_type": event.source_type,
                    "status": event.status,
                }
                for event in timeline.events
            ],
            "gaps": [gap.model_dump() for gap in timeline.gaps],
            "inferred_events": [
                inferred.model_dump()
                for inferred in timeline.inferred_events
            ],
        },
        "evidence": [
            {
                "evidence_id": item.id,
                "title": item.title,
                "source_name": item.source_name,
                "evidence_type": item.evidence_type,
                "summary": item.summary,
                "confidence_score": item.confidence_score,
                "extraction_method": item.extraction_method,
                "uncertainty_notes": item.uncertainty_notes or [],
            }
            for item in evidence_items
        ],
        "contradictions": {
            "total_findings": contradictions.total_findings,
            "highest_severity": contradictions.highest_severity,
            "findings": [
                {
                    "type": finding.contradiction_type,
                    "severity": finding.severity,
                    "description": finding.description,
                    "explanation": finding.explanation,
                    "confidence_score": finding.confidence_score,
                    "involved_event_ids": finding.involved_event_ids,
                    "involved_evidence_ids": finding.involved_evidence_ids,
                    "recommended_review_action": finding.recommended_review_action,
                }
                for finding in contradictions.findings
            ],
        },
        "hypotheses": {
            "generation_method": hypotheses.generation_method,
            "total_scenarios": hypotheses.total_scenarios,
            "highest_confidence_scenario_id": hypotheses.highest_confidence_scenario_id,
            "scenarios": [
                {
                    "scenario_id": scenario.scenario_id,
                    "title": scenario.title,
                    "description": scenario.description,
                    "confidence_score": scenario.confidence_score,
                    "supporting_event_ids": scenario.supporting_event_ids,
                    "supporting_evidence_ids": scenario.supporting_evidence_ids,
                    "assumptions": scenario.assumptions,
                    "contradictions": scenario.contradictions,
                    "missing_evidence": scenario.missing_evidence,
                    "recommended_validation": scenario.recommended_validation,
                }
                for scenario in hypotheses.scenarios
            ],
            "uncertainty_notice": hypotheses.uncertainty_notice,
        },
    }

def generate_rule_based_assistant_answer(
    db: Session,
    case_id: int,
    question: str,
) -> AssistantAnswer:
    question_lower = question.lower()

    if any(keyword in question_lower for keyword in ["evidence", "source", "witness", "support", "supports"]):
        return answer_evidence_question(db=db, case_id=case_id, question=question)

    if any(keyword in question_lower for keyword in ["contradiction", "conflict", "inconsistent", "suspicious"]):
        return answer_contradiction_question(db=db, case_id=case_id, question=question)

    if any(keyword in question_lower for keyword in ["hypothesis", "scenario", "likely", "possible"]):
        return answer_hypothesis_question(db=db, case_id=case_id, question=question)

    if any(keyword in question_lower for keyword in ["timeline", "happened", "between", "sequence"]):
        return answer_timeline_question(db=db, case_id=case_id, question=question)

    return answer_general_case_question(db=db, case_id=case_id, question=question)

def generate_assistant_answer(
    db: Session,
    case_id: int,
    question: str,
) -> AssistantAnswer:
    if settings.USE_LLM_ASSISTANT and settings.OPENAI_API_KEY:
        try:
            case_context = build_case_context_for_assistant(
                db=db,
                case_id=case_id,
            )

            llm_result = answer_question_with_llm(
                question=question,
                case_context=case_context,
            )

            return convert_llm_assistant_result(
                case_id=case_id,
                question=question,
                llm_result=llm_result,
            )
        except Exception as exc:
            fallback_answer = generate_rule_based_assistant_answer(
                db=db,
                case_id=case_id,
                question=question,
            )
            fallback_answer.generation_method = "rule_based_fallback"
            fallback_answer.llm_error = str(exc)
            return fallback_answer

    fallback_answer = generate_rule_based_assistant_answer(
        db=db,
        case_id=case_id,
        question=question,
    )
    fallback_answer.generation_method = "rule_based"
    fallback_answer.llm_error = None

    return fallback_answer

def convert_llm_assistant_result(
    case_id: int,
    question: str,
    llm_result,
) -> AssistantAnswer:
    return AssistantAnswer(
        case_id=case_id,
        question=question,
        answer=llm_result.answer,
        confidence_score=llm_result.confidence_score,
        evidence_references=llm_result.evidence_references,
        limitations=llm_result.limitations,
        suggested_follow_up_questions=llm_result.suggested_follow_up_questions,
        generation_method="llm",
        llm_error=None,
    )