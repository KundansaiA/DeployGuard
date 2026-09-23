"""Unit tests for the AI explanation abstraction (base types)."""
from app.ai.base import (
    AnalysisContext,
    ExplanationResult,
    SignalSummary,
)


def test_explanation_result_done() -> None:
    result = ExplanationResult(status="done", text="This is safe to deploy.")
    assert result.status == "done"
    assert result.text == "This is safe to deploy."
    assert result.error is None


def test_explanation_result_failed() -> None:
    result = ExplanationResult(status="failed", error="timeout")
    assert result.status == "failed"
    assert result.text is None
    assert result.error == "timeout"


def test_analysis_context_built_correctly() -> None:
    signal = SignalSummary(
        signal_type="LARGE_CHANGE",
        severity="HIGH",
        title="Large change",
        description="Many files changed",
        score_contribution=25.0,
        evidence={"files_changed": 30},
    )
    ctx = AnalysisContext(
        analysis_id="abc-123",
        repository="org/repo",
        branch="main",
        commit_sha="abc1234",
        risk_score=65.0,
        severity="HIGH",
        total_files_changed=30,
        total_additions=400,
        total_deletions=100,
        signals=[signal],
    )
    assert ctx.analysis_id == "abc-123"
    assert len(ctx.signals) == 1
    assert ctx.signals[0].signal_type == "LARGE_CHANGE"
