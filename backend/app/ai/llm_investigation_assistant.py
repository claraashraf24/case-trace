import json
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ai_assistant import LLMAssistantResult


SYSTEM_PROMPT = """
You are an AI investigation assistant for CaseTrace AI.

Your role:
Assist analysts in understanding fragmented incident evidence.

Important safety and quality rules:
- Do not claim final truth.
- Do not say someone is guilty, responsible, or intentionally suspicious.
- Use cautious language: "may", "could", "appears", "requires validation".
- Ground every answer in the provided case context.
- Mention uncertainty when evidence is approximate or incomplete.
- Prefer evidence IDs, event IDs, and source names when available.
- If the question cannot be answered from the context, say what evidence is missing.
- Keep answers clear and concise.
"""


ASSISTANT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answer": {
            "type": "string",
        },
        "confidence_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
        },
        "evidence_references": {
            "type": "array",
            "items": {"type": "string"},
        },
        "limitations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "suggested_follow_up_questions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "answer",
        "confidence_score",
        "evidence_references",
        "limitations",
        "suggested_follow_up_questions",
    ],
}


def get_openai_client() -> OpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None

    return OpenAI(api_key=settings.OPENAI_API_KEY)


def build_assistant_prompt(question: str, case_context: dict[str, Any]) -> str:
    return f"""
Answer the user's question using only the case context below.

USER QUESTION:
{question}

CASE CONTEXT JSON:
{json.dumps(case_context, indent=2)}

Response requirements:
- Answer the question directly.
- Use evidence references when possible.
- Include uncertainty and limitations.
- Do not invent facts outside the case context.
- Do not make final conclusions.
"""


def parse_json_from_response(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM assistant response was not valid JSON.") from exc


def answer_question_with_llm(
    question: str,
    case_context: dict[str, Any],
) -> LLMAssistantResult:
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
                "content": build_assistant_prompt(
                    question=question,
                    case_context=case_context,
                ),
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "assistant_answer",
                "schema": ASSISTANT_SCHEMA,
                "strict": True,
            }
        },
    )

    parsed_json = parse_json_from_response(response.output_text)

    try:
        return LLMAssistantResult.model_validate(parsed_json)
    except ValidationError as exc:
        raise ValueError("LLM assistant response did not match schema.") from exc