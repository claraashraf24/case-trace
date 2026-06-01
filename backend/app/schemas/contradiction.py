from typing import Optional

from pydantic import BaseModel


class ContradictionFinding(BaseModel):
    contradiction_type: str
    severity: str
    involved_event_ids: list[int]
    involved_evidence_ids: list[int]
    description: str
    explanation: str
    confidence_score: float
    recommended_review_action: str


class ContradictionSummary(BaseModel):
    case_id: int
    total_findings: int
    highest_severity: Optional[str] = None
    has_critical_contradictions: bool
    findings: list[ContradictionFinding]

class ContradictionReport(BaseModel):
    case_id: int
    report_title: str
    executive_summary: str
    risk_level: str
    total_findings: int
    key_findings: list[str]
    recommended_actions: list[str]
    uncertainty_notice: str