from pydantic import BaseModel


class HypothesisScenario(BaseModel):
    scenario_id: str
    title: str
    description: str
    confidence_score: float
    supporting_event_ids: list[int]
    supporting_evidence_ids: list[int]
    assumptions: list[str]
    contradictions: list[str]
    missing_evidence: list[str]
    recommended_validation: list[str]


class HypothesisResult(BaseModel):
    case_id: int
    total_scenarios: int
    highest_confidence_scenario_id: str | None
    generation_method: str | None = None
    scenarios: list[HypothesisScenario]
    uncertainty_notice: str
    llm_error: str | None = None