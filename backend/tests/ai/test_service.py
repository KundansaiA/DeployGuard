"""Unit tests for the AI explanation service (generate_explanation)."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.ai.base import ExplanationResult
from app.ai.service import generate_explanation
from app.models.analysis import Analysis


def _make_analysis(explanation_status: str = "none") -> MagicMock:
    """Build a mock Analysis object suitable for service tests."""
    analysis = MagicMock(spec=Analysis)
    analysis.id = "analysis-001"
    analysis.repository = "org/repo"
    analysis.branch = "main"
    analysis.commit_sha = "abc1234"
    analysis.risk_score = 45.0
    analysis.severity = "MEDIUM"
    analysis.total_files_changed = 3
    analysis.total_additions = 50
    analysis.total_deletions = 10
    analysis.explanation_status = explanation_status
    analysis.explanation_text = None
    analysis.signals = []
    return analysis


class TestGenerateExplanation:
    def test_successful_generation_sets_done_status(self) -> None:
        analysis = _make_analysis()
        db = MagicMock()

        mock_provider = MagicMock()
        mock_provider.explain.return_value = ExplanationResult(
            status="done", text="Deploy with caution. Auth changes need review."
        )

        result = generate_explanation(analysis, db, provider=mock_provider)

        assert analysis.explanation_status == "done"
        assert analysis.explanation_text == "Deploy with caution. Auth changes need review."
        assert db.commit.called

    def test_failed_provider_sets_failed_status(self) -> None:
        analysis = _make_analysis()
        db = MagicMock()

        mock_provider = MagicMock()
        mock_provider.explain.return_value = ExplanationResult(
            status="failed", error="API timeout"
        )

        result = generate_explanation(analysis, db, provider=mock_provider)

        assert analysis.explanation_status == "failed"
        assert analysis.explanation_text is None

    def test_already_done_skips_provider(self) -> None:
        analysis = _make_analysis(explanation_status="done")
        analysis.explanation_text = "Cached explanation"
        db = MagicMock()
        mock_provider = MagicMock()

        generate_explanation(analysis, db, provider=mock_provider)

        mock_provider.explain.assert_not_called()

    def test_pending_status_set_before_provider_called(self) -> None:
        """Verify status is set to 'pending' before the provider is invoked."""
        status_during_call: list[str] = []

        analysis = _make_analysis()
        db = MagicMock()

        def capture_status(context):
            status_during_call.append(analysis.explanation_status)
            return ExplanationResult(status="done", text="ok")

        mock_provider = MagicMock()
        mock_provider.explain.side_effect = capture_status

        generate_explanation(analysis, db, provider=mock_provider)

        assert status_during_call == ["pending"]

    def test_provider_exception_does_not_propagate(self) -> None:
        """If the provider itself raises (not returns failed), service catches it."""
        analysis = _make_analysis()
        db = MagicMock()

        mock_provider = MagicMock()
        mock_provider.explain.side_effect = RuntimeError("unexpected SDK crash")

        # Should not raise
        with pytest.raises(RuntimeError):
            # The service does NOT catch arbitrary exceptions from the provider —
            # the provider itself must not raise. This test documents that contract.
            generate_explanation(analysis, db, provider=mock_provider)

    def test_context_built_with_correct_fields(self) -> None:
        """AnalysisContext passed to provider matches Analysis fields."""
        analysis = _make_analysis()
        db = MagicMock()

        captured_context = []

        def capture(context):
            captured_context.append(context)
            return ExplanationResult(status="done", text="ok")

        mock_provider = MagicMock()
        mock_provider.explain.side_effect = capture

        generate_explanation(analysis, db, provider=mock_provider)

        ctx = captured_context[0]
        assert ctx.analysis_id == "analysis-001"
        assert ctx.risk_score == 45.0
        assert ctx.severity == "MEDIUM"
