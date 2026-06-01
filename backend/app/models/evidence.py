from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base


class EvidenceType(str, Enum):
    WITNESS_STATEMENT = "witness_statement"
    INCIDENT_REPORT = "incident_report"
    CALL_TRANSCRIPT = "call_transcript"
    GPS_LOG = "gps_log"
    CCTV_SUMMARY = "cctv_summary"
    CHAT_LOG = "chat_log"
    PHONE_LOG = "phone_log"
    FORENSIC_NOTE = "forensic_note"
    OTHER = "other"


class EvidenceStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=EvidenceType.OTHER.value,
    )

    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=EvidenceStatus.UPLOADED.value,
    )

    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uncertainty_notes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    case = relationship("Case", back_populates="evidence_items")
    events = relationship("Event", back_populates="evidence")