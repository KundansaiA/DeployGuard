"""Analysis pipeline service.

Orchestrates the full analysis workflow:
  ChangePayload → run all analyzers → engine → persist → return Analysis ORM object

This is the only module that writes to the database.
Analyzers and the engine are called as pure functions here.
"""
import uuid

from sqlalchemy.orm import Session

from app.analyzers import Analyzer, RiskSignal, build_analyzer_registry
from app.engine import run_engine
from app.ingestion.types import ChangePayload
from app.models.analysis import Analysis, RiskSignalRecord, SeverityTier
from app.schemas.analysis import SubmitChangeRequest
from app.ingestion.normalise import normalise_change


def _run_analyzers(
    change: ChangePayload,
    analyzers: list[Analyzer],
) -> list[RiskSignal]:
    """Run all analyzers and collect every signal they produce."""
    signals: list[RiskSignal] = []
    for analyzer in analyzers:
        signals.extend(analyzer.analyze(change))
    return signals


def _persist_analysis(
    db: Session,
    change: ChangePayload,
    signals: list[RiskSignal],
    score: float,
    severity: SeverityTier,
) -> Analysis:
    """Create and persist an Analysis and its RiskSignalRecords."""
    analysis_id = str(uuid.uuid4())

    analysis = Analysis(
        id=analysis_id,
        repository=change.repository,
        branch=change.branch,
        commit_sha=change.commit_sha,
        total_files_changed=change.total_files,
        total_additions=change.total_additions,
        total_deletions=change.total_deletions,
        risk_score=score,
        severity=severity.value,
        explanation_text=None,
        explanation_status="none",
    )
    db.add(analysis)

    for signal in signals:
        record = RiskSignalRecord(
            id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            signal_type=signal.signal_type,
            severity=signal.severity.value,
            title=signal.title,
            description=signal.description,
            evidence=signal.evidence,
            score_contribution=signal.score_contribution,
            source_analyzer=signal.source_analyzer,
        )
        db.add(record)

    db.commit()
    db.refresh(analysis)
    return analysis


def run_analysis(
    request: SubmitChangeRequest,
    db: Session,
    analyzers: list[Analyzer] | None = None,
) -> Analysis:
    """Full pipeline: ingest → analyse → score → persist → return.

    Args:
        request: Validated API request payload.
        db: SQLAlchemy session (injected by FastAPI dependency).
        analyzers: Analyzer list (defaults to the registry). Injectable for testing.

    Returns:
        Persisted Analysis ORM object with signals loaded.
    """
    if analyzers is None:
        analyzers = build_analyzer_registry()

    change = normalise_change(request)
    signals = _run_analyzers(change, analyzers)
    result = run_engine(signals)

    return _persist_analysis(
        db=db,
        change=change,
        signals=result.signals,
        score=result.score,
        severity=result.severity,
    )
