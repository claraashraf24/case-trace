from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CaseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    summary: Optional[str] = None
    case_type: str = "general_incident"
    priority: str = "medium"
    status: str = "open"
    location: Optional[str] = None
    incident_date: Optional[datetime] = None


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    summary: Optional[str] = None
    case_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    incident_date: Optional[datetime] = None


class CaseRead(CaseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class CaseStats(BaseModel):
    total_cases: int

    open_cases: int
    in_review_cases: int
    closed_cases: int
    archived_cases: int

    critical_priority_cases: int
    high_priority_cases: int
    medium_priority_cases: int
    low_priority_cases: int