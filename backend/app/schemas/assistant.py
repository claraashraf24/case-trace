from pydantic import BaseModel, Field


class AssistantQuery(BaseModel):
    question: str = Field(..., min_length=3)


class AssistantAnswer(BaseModel):
    case_id: int
    question: str
    answer: str
    confidence_score: float
    evidence_references: list[str]
    limitations: list[str]
    suggested_follow_up_questions: list[str]
    generation_method: str | None = None
    llm_error: str | None = None