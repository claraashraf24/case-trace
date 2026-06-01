from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    event_time: Optional[str] = None
    normalized_time: Optional[datetime] = None
    location: Optional[str] = None
    description: str = Field(..., min_length=3)

    participants: Optional[list[Any]] = None
    actions: Optional[list[Any]] = None
    objects: Optional[list[Any]] = None

    confidence_score: float = Field(0, ge=0, le=100)
    source_type: str = "extracted"
    status: str = "draft"


class EventCreate(EventBase):
    case_id: int
    evidence_id: Optional[int] = None


class EventUpdate(BaseModel):
    event_time: Optional[str] = None
    normalized_time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = Field(None, min_length=3)

    participants: Optional[list[Any]] = None
    actions: Optional[list[Any]] = None
    objects: Optional[list[Any]] = None

    confidence_score: Optional[float] = Field(None, ge=0, le=100)
    source_type: Optional[str] = None
    status: Optional[str] = None


class EventRead(EventBase):
    id: int
    case_id: int
    evidence_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }