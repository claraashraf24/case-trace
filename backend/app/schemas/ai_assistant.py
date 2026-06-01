from pydantic import BaseModel, Field


class LLMAssistantResult(BaseModel):
    answer: str
    confidence_score: int = Field(ge=0, le=100)
    evidence_references: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    suggested_follow_up_questions: list[str] = Field(default_factory=list)