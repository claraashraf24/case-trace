from pydantic import BaseModel, Field


class LLMHypothesisScenario(BaseModel):
    scenario_id: str
    title: str
    description: str
    confidence_score: int = Field(ge=0, le=100)
    supporting_event_ids: list[int] = Field(default_factory=list)
    supporting_evidence_ids: list[int] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    recommended_validation: list[str] = Field(default_factory=list)


class LLMHypothesisResult(BaseModel):
    scenarios: list[LLMHypothesisScenario] = Field(default_factory=list)
    uncertainty_notice: str