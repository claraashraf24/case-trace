from pydantic import BaseModel, Field


class LLMNormalizedEvent(BaseModel):
    time: str | None = None
    location: str | None = None
    participants: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    objects: list[str] = Field(default_factory=list)
    description: str
    confidence: int = Field(ge=0, le=100)


class LLMEvidenceExtraction(BaseModel):
    people: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    timestamps: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    objects: list[str] = Field(default_factory=list)
    normalized_event: LLMNormalizedEvent
    uncertainty_notes: list[str] = Field(default_factory=list)