"""Pydantic v2 schemas for the analysis API."""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.analysis import SeverityTier


# ─────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────


class ChangeFileSchema(BaseModel):
    """A single changed file within a software change."""

    path: str = Field(..., description="File path relative to repo root")
    additions: int = Field(0, ge=0, description="Lines added")
    deletions: int = Field(0, ge=0, description="Lines deleted")
    patch: str | None = Field(None, description="Optional unified diff patch")


class SubmitChangeRequest(BaseModel):
    """Payload submitted to POST /api/v1/analyses."""

    repository: str = Field(..., min_length=1, description="Repository identifier, e.g. org/repo")
    branch: str = Field(..., min_length=1, description="Branch name")
    commit_sha: str = Field(..., min_length=7, max_length=40, description="Commit SHA (full or short)")
    changed_files: list[ChangeFileSchema] = Field(
        default_factory=list, description="List of changed files"
    )

    @field_validator("commit_sha")
    @classmethod
    def commit_sha_alphanumeric(cls, v: str) -> str:
        if not all(c in "0123456789abcdefABCDEF" for c in v):
            raise ValueError("commit_sha must be a hexadecimal string")
        return v.lower()


# ─────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────


class RiskSignalResponse(BaseModel):
    """A single risk signal returned in an analysis response."""

    id: str
    signal_type: str
    severity: SeverityTier
    title: str
    description: str
    evidence: dict | None
    score_contribution: float
    source_analyzer: str

    model_config = {"from_attributes": True}


class ExplanationResponse(BaseModel):
    """Explanation sub-object returned on an analysis."""

    status: str  # "none" | "pending" | "done" | "failed"
    text: str | None


class AnalysisResponse(BaseModel):
    """Full analysis result returned to the caller."""

    id: str
    repository: str
    branch: str
    commit_sha: str
    total_files_changed: int
    total_additions: int
    total_deletions: int
    risk_score: float
    severity: SeverityTier
    explanation_text: str | None
    explanation_status: str
    created_at: datetime
    signals: list[RiskSignalResponse]

    model_config = {"from_attributes": True}


class AnalysisListResponse(BaseModel):
    """Paginated list of analyses."""

    items: list[AnalysisResponse]
    total: int
