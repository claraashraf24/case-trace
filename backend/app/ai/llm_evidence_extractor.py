import json
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ai_extraction import LLMEvidenceExtraction


SYSTEM_PROMPT = """
You are an evidence extraction assistant for an incident reconstruction platform.

Your task:
Extract structured entities and one normalized event from the evidence text.

Important rules:
- Do not invent facts.
- If a detail is uncertain, include it in uncertainty_notes.
- Use cautious language.
- Confidence should reflect extraction quality, not truth.
- This system assists analysts; it does not determine guilt, intent, or final truth.
- Return only structured JSON matching the schema.
"""


EVIDENCE_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "people": {
            "type": "array",
            "items": {"type": "string"},
        },
        "locations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "timestamps": {
            "type": "array",
            "items": {"type": "string"},
        },
        "actions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "objects": {
            "type": "array",
            "items": {"type": "string"},
        },
        "normalized_event": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "time": {
                    "type": ["string", "null"],
                },
                "location": {
                    "type": ["string", "null"],
                },
                "participants": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "actions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "objects": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "description": {
                    "type": "string",
                },
                "confidence": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": [
                "time",
                "location",
                "participants",
                "actions",
                "objects",
                "description",
                "confidence",
            ],
        },
        "uncertainty_notes": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "people",
        "locations",
        "timestamps",
        "actions",
        "objects",
        "normalized_event",
        "uncertainty_notes",
    ],
}


def build_extraction_prompt(evidence_text: str) -> str:
    return f"""
Extract structured incident information from this evidence text.

EVIDENCE TEXT:
{evidence_text}

Return:
- people
- locations
- timestamps
- actions
- objects
- normalized_event
- uncertainty_notes

The normalized_event should represent the main event described by the evidence.
"""


def get_openai_client() -> OpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None

    return OpenAI(api_key=settings.OPENAI_API_KEY)


def parse_json_from_response(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response was not valid JSON.") from exc


def extract_evidence_with_llm(evidence_text: str) -> LLMEvidenceExtraction:
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
                "content": build_extraction_prompt(evidence_text),
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "evidence_extraction",
                "schema": EVIDENCE_EXTRACTION_SCHEMA,
                "strict": True,
            }
        },
    )

    parsed_json = parse_json_from_response(response.output_text)

    try:
        return LLMEvidenceExtraction.model_validate(parsed_json)
    except ValidationError as exc:
        raise ValueError("LLM response did not match extraction schema.") from exc