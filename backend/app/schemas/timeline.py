from typing import Any, Optional

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    event_id: int
    evidence_id: Optional[int] = None
    event_time: Optional[str] = None
    location: Optional[str] = None
    description: str
    participants: list[Any] | None = None
    actions: list[Any] | None = None
    objects: list[Any] | None = None
    confidence_score: float
    source_type: str
    status: str


class TimelineGap(BaseModel):
    from_event_id: int
    to_event_id: int
    from_time: Optional[str] = None
    to_time: Optional[str] = None
    gap_minutes: Optional[int] = None
    message: str

class InferredTimelineEvent(BaseModel):
    inferred_time_window: str
    between_event_ids: list[int]
    inference_type: str
    description: str
    supporting_reason: str
    confidence_score: float


class TimelineConfidence(BaseModel):
    average_confidence: float
    lowest_confidence: float
    highest_confidence: float
    total_events: int

class TimelineRiskAssessment(BaseModel):
    timeline_risk_label: str
    timeline_quality_score: float
    review_flags: list[str]


class TimelineReconstruction(BaseModel):
    case_id: int
    total_events: int
    timeline_summary: str
    events: list[TimelineEvent]
    gaps: list[TimelineGap]
    inferred_events: list[InferredTimelineEvent]
    confidence: TimelineConfidence
    risk_assessment: TimelineRiskAssessment

class TimelineReport(BaseModel):
    case_id: int
    report_title: str
    executive_summary: str
    key_events: list[str]
    timeline_gaps: list[str]
    inferred_missing_events: list[str]
    risk_label: str
    quality_score: float
    recommended_next_steps: list[str]
    uncertainty_notice: str