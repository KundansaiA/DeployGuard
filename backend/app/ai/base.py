"""AI explanation abstraction layer.

Defines the provider protocol and shared types.  Application code must
depend only on these interfaces — never on a concrete provider directly.

Architecture
────────────
  AnalysisContext          — structured input built from a persisted Analysis
  ExplanationResult        — structured output from any provider
  ExplanationProvider      — Protocol every provider must satisfy
  ExplanationStatus        — string literal type for status field values
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


ExplanationStatus = Literal["none", "pending", "done", "failed"]


@dataclass(frozen=True)
class SignalSummary:
    """Condensed view of a single risk signal passed to the AI provider."""

    signal_type: str
    severity: str
    title: str
    description: str
    score_contribution: float
    evidence: dict = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisContext:
    """All deterministic findings passed to the AI provider.

    This is constructed from a persisted Analysis ORM object and is the
    only input the provider receives.  It contains facts, not opinions.
    """

    analysis_id: str
    repository: str
    branch: str
    commit_sha: str
    risk_score: float
    severity: str
    total_files_changed: int
    total_additions: int
    total_deletions: int
    signals: list[SignalSummary] = field(default_factory=list)


@dataclass
class ExplanationResult:
    """Output from an AI explanation provider.

    Fields
    ──────
    text        — the generated explanation (None when unavailable)
    status      — final status: "done" or "failed"
    error       — human-readable error message when status == "failed"
    """

    status: ExplanationStatus
    text: str | None = None
    error: str | None = None


class ExplanationProvider(Protocol):
    """Protocol every AI explanation provider must satisfy.

    A provider receives a fully-determined AnalysisContext and returns
    an ExplanationResult.  It must NEVER alter the risk score or signals.
    """

    def explain(self, context: AnalysisContext) -> ExplanationResult:
        """Generate a human-readable explanation for the given analysis context."""
        ...
