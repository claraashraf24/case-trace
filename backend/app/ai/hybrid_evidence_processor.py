from typing import Any

from app.ai.evidence_extractor import process_evidence_text
from app.ai.llm_evidence_extractor import extract_evidence_with_llm
from app.core.config import settings


def convert_llm_result_to_processing_result(
    evidence_id: int,
    raw_text: str,
    llm_result,
) -> dict[str, Any]:
    event = llm_result.normalized_event

    return {
        "evidence_id": evidence_id,
        "extraction_method": "llm",
        "entities": {
            "people": llm_result.people,
            "locations": llm_result.locations,
            "timestamps": llm_result.timestamps,
            "actions": llm_result.actions,
            "objects": llm_result.objects,
        },
        "event_draft": {
            "evidence_id": evidence_id,
            "time": event.time,
            "location": event.location,
            "participants": event.participants,
            "actions": event.actions,
            "objects": event.objects,
            "description": event.description or raw_text,
            "confidence": event.confidence,
        },
        "uncertainty_notes": llm_result.uncertainty_notes,
    }


def process_evidence_text_hybrid(
    evidence_id: int,
    text: str,
) -> dict[str, Any]:
    if settings.USE_LLM_EXTRACTION and settings.OPENAI_API_KEY:
        try:
            llm_result = extract_evidence_with_llm(evidence_text=text)
            return convert_llm_result_to_processing_result(
                evidence_id=evidence_id,
                raw_text=text,
                llm_result=llm_result,
            )
        except Exception as exc:
            fallback_result = process_evidence_text(
                evidence_id=evidence_id,
                text=text,
            )
            fallback_result["extraction_method"] = "rule_based_fallback"
            fallback_result["llm_error"] = str(exc)
            return fallback_result

    fallback_result = process_evidence_text(
        evidence_id=evidence_id,
        text=text,
    )
    fallback_result["extraction_method"] = "rule_based"
    return fallback_result