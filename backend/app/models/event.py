from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    evidence_id: Mapped[int | None] = mapped_column(
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    event_time: Mapped[str | None] = mapped_column(String(100), nullable=True)
    normalized_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    participants: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    actions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    objects: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    source_type: Mapped[str] = mapped_column(String(100), nullable=False, default="extracted")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")

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

    case = relationship("Case", back_populates="events")
    evidence = relationship("Evidence", back_populates="events")