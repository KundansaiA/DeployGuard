"""AI explanation service.

Bridges the application (Analysis ORM objects) and the AI provider layer.
All business logic for generating, persisting, and retrieving explanations
lives here — never in route handlers or providers.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.ai.base import AnalysisContext, ExplanationProvider, SignalSummary
from app.ai.watsonx import get_default_provider
from app.models.analysis import Analysis

logger = logging.getLogger(__name__)


def _build_context(analysis: Analysis) -> AnalysisContext:
    """Convert a persisted Analysis ORM object into an AnalysisContext for the provider."""
    signals = [
        SignalSummary(
            signal_type=s.signal_type,
            severity=s.severity,
            title=s.title,
            description=s.description,
            score_contribution=s.score_contribution,
            evidence=s.evidence or {},
        )
        for s in (analysis.signals or [])
    ]
    return AnalysisContext(
        analysis_id=analysis.id,
        repository=analysis.repository,
        branch=analysis.branch,
        commit_sha=analysis.commit_sha,
        risk_score=analysis.risk_score,
        severity=analysis.severity,
        total_files_changed=analysis.total_files_changed,
        total_additions=analysis.total_additions,
        total_deletions=analysis.total_deletions,
        signals=signals,
    )


def generate_explanation(
    analysis: Analysis,
    db: Session,
    provider: ExplanationProvider | None = None,
) -> Analysis:
    """Generate an AI explanation for a completed analysis and persist it.

    Behaviour
    ─────────
    - If explanation_status is already "done", returns immediately (idempotent).
    - Sets status to "pending" before calling the provider.
    - On provider success: sets explanation_text and status "done".
    - On provider failure: sets status "failed", explanation_text = None.
    - The Analysis is always committed and returned — the deterministic result
      is never affected by provider failures.

    Args:
        analysis: Persisted Analysis ORM object (must already be in session).
        db:       Active SQLAlchemy session.
        provider: AI provider to use (defaults to WatsonxGraniteProvider).

    Returns:
        The updated Analysis object.
    """
    if analysis.explanation_status == "done":
        logger.debug("Explanation already generated for analysis %s, skipping", analysis.id)
        return analysis

    if provider is None:
        provider = get_default_provider()

    # Mark as pending so concurrent calls don't double-generate
    analysis.explanation_status = "pending"
    db.commit()

    context = _build_context(analysis)
    result = provider.explain(context)

    analysis.explanation_text = result.text
    analysis.explanation_status = result.status
    db.commit()
    db.refresh(analysis)

    if result.status == "failed":
        logger.warning(
            "Explanation generation failed for analysis %s: %s",
            analysis.id,
            result.error,
        )
    else:
        logger.info("Explanation generated for analysis %s", analysis.id)

    return analysis
