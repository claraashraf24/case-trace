from pydantic import BaseModel


class MovementPoint(BaseModel):
    event_id: int
    evidence_id: int | None = None
    event_time: str | None = None
    label: str
    location: str | None = None
    zone: str | None = None
    x: float
    y: float
    confidence_score: float
    source_type: str
    description: str


class MovementSegment(BaseModel):
    from_event_id: int
    to_event_id: int
    from_time: str | None = None
    to_time: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    distance_label: str
    time_gap_minutes: int | None = None
    is_suspicious: bool
    alert: str | None = None


class MovementReconstructionResponse(BaseModel):
    case_id: int
    total_points: int
    total_segments: int
    points: list[MovementPoint]
    segments: list[MovementSegment]
    summary: str