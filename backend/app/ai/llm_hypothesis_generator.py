import json
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ai_hypothesis import LLMHypothesisResult


SYSTEM_PROMPT = """
You are an analytical hypothesis generation assistant for an incident reconstruction platform.

Your task:
Generate multiple possible incident hypotheses from structured evidence, timeline events,
contradiction findings, confidence scores, and uncertainty notes.

Important rules:
- Do not claim what definitely happened.
- Do not assign guilt, blame, criminal responsibility, intent, motive, or emotional state.
- Do not infer that a person was calm, guilty, afraid, aggressive, suspicious, or intentionally leaving unless the evidence explicitly says that.
- If evidence says a person "looked nervous", phrase it as "was reported as looking nervous" or "was described as appearing nervous".
- Use cautious language such as "may", "could", "appears", "reported", "requires validation".
- Every scenario must be grounded in event IDs and evidence IDs when available.
- Include assumptions, contradictions, missing evidence, and recommended validation.
- Confidence means analytical support strength, not truth.
- Keep the output professional and useful for human investigators/analysts.
- Avoid dramatic storytelling. Keep scenarios neutral, evidence-based, and concise.
"""


HYPOTHESIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "scenarios": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "scenario_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "confidence_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "supporting_event_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                    "supporting_evidence_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                    "assumptions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "contradictions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "missing_evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "recommended_validation": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "scenario_id",
                    "title",
                    "description",
                    "confidence_score",
                    "supporting_event_ids",
                    "supporting_evidence_ids",
                    "assumptions",
                    "contradictions",
                    "missing_evidence",
                    "recommended_validation",
                ],
            },
        },
        "uncertainty_notice": {"type": "string"},
    },
    "required": ["scenarios", "uncertainty_notice"],
}


def get_openai_client() -> OpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None

    return OpenAI(api_key=settings.OPENAI_API_KEY)


def build_hypothesis_prompt(case_context: dict[str, Any]) -> str:
    return f"""
Generate 2 to 3 possible analytical hypotheses from this case context.

CASE CONTEXT JSON:
{json.dumps(case_context, indent=2)}

Requirements:
- Generate scenario IDs like scenario_a, scenario_b, scenario_c.
- Do not invent evidence IDs or event IDs.
- Use only the events/evidence/contradictions provided.
- Do not infer intent, motive, guilt, blame, or emotional state.
- If describing behavior, attribute it to evidence. Example: say "Witness C reported John appeared nervous", not "John was nervous".
- Do not use unsupported words like "calmly", "decided", "wanted", "intended", "fled", or "escaped".
- If a scenario depends on uncertain timing or location data, say it requires validation.
- Mention missing evidence clearly.
- Avoid final conclusions.
- Keep each scenario description between 2 and 4 sentences.
"""


def parse_json_from_response(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM hypothesis response was not valid JSON.") from exc


def generate_hypotheses_with_llm(case_context: dict[str, Any]) -> LLMHypothesisResult:
    client = get_openai_client()

    if not client:
        raise ValueError("OPENAI_API_KEY is not configured.")

    response = client.responses.create(
        model=settings.OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_hypothesis_prompt(case_context),
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "hypothesis_generation",
                "schema": HYPOTHESIS_SCHEMA,
                "strict": True,
            }
        },
    )

    parsed_json = parse_json_from_response(response.output_text)

    try:
        return LLMHypothesisResult.model_validate(parsed_json)
    except ValidationError as exc:
        raise ValueError("LLM hypothesis response did not match schema.") from exc