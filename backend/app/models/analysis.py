"""SQLAlchemy ORM models for analysis domain."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SeverityTier(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    repository: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str] = mapped_column(String(255), nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    total_files_changed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_additions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_deletions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # Stored as String for cross-DB compatibility (SQLite + PostgreSQL)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SeverityTier.LOW.value
    )
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # explanation_status tracks AI generation state: "none" | "pending" | "done" | "failed"
    explanation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="none"
    )
    # Python-side default ensures SQLite tests work without server-side RETURNING
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )

    signals: Mapped[list["RiskSignalRecord"]] = relationship(
        "RiskSignalRecord", back_populates="analysis", cascade="all, delete-orphan"
    )


class RiskSignalRecord(Base):
    __tablename__ = "risk_signals"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score_contribution: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_analyzer: Mapped[str] = mapped_column(String(100), nullable=False)

    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="signals")
