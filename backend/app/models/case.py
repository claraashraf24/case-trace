from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CaseStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CasePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    case_type: Mapped[str] = mapped_column(String(100), nullable=False, default="general_incident")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=CaseStatus.OPEN.value)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default=CasePriority.MEDIUM.value)

    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    incident_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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

    evidence_items = relationship(
        "Evidence",
        back_populates="case",
        cascade="all, delete-orphan",
    )

    events = relationship(
        "Event",
        back_populates="case",
        cascade="all, delete-orphan",
    )