from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EvidenceBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    evidence_type: str = "other"

    source_name: Optional[str] = None
    source_reference: Optional[str] = None

    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_path: Optional[str] = None

    raw_text: Optional[str] = None
    summary: Optional[str] = None

    status: str = "uploaded"
    confidence_score: Optional[int] = Field(None, ge=0, le=100)
    extraction_method: Optional[str] = None
    uncertainty_notes: Optional[list[str]] = None
    notes: Optional[str] = None


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    evidence_type: Optional[str] = None

    source_name: Optional[str] = None
    source_reference: Optional[str] = None

    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_path: Optional[str] = None

    raw_text: Optional[str] = None
    summary: Optional[str] = None

    status: Optional[str] = None
    confidence_score: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class EvidenceRead(EvidenceBase):
    id: int
    case_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class ExtractedEntities(BaseModel):
    people: list[str]
    locations: list[str]
    timestamps: list[str]
    actions: list[str]
    objects: list[str]


class EventDraft(BaseModel):
    evidence_id: int
    time: Optional[str] = None
    location: Optional[str] = None
    participants: list[str]
    actions: list[str]
    objects: list[str]
    description: str
    confidence: int


class EvidenceProcessingResult(BaseModel):
    evidence_id: int
    extraction_method: str | None = None
    entities: ExtractedEntities
    event_draft: EventDraft
    uncertainty_notes: list[str] | None = None
    llm_error: str | None = None