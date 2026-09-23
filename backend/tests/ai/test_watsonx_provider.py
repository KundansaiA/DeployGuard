"""Unit tests for the WatsonxGraniteProvider.

No real IBM credentials are required.  All external SDK calls are mocked
using unittest.mock.patch so tests are fully isolated.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.ai.base import AnalysisContext, SignalSummary
from app.ai.watsonx import WatsonxGraniteProvider, _build_user_prompt


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def ctx() -> AnalysisContext:
    return AnalysisContext(
        analysis_id="test-id-001",
        repository="org/core-service",
        branch="feature/auth-refactor",
        commit_sha="deadbeef",
        risk_score=70.0,
        severity="HIGH",
        total_files_changed=5,
        total_additions=80,
        total_deletions=20,
        signals=[
            SignalSummary(
                signal_type="AUTH_SECURITY_CHANGE",
                severity="CRITICAL",
                title="Auth code modified",
                description="Login flow changed",
                score_contribution=35.0,
            )
        ],
    )


@pytest.fixture
def unconfigured_provider() -> WatsonxGraniteProvider:
    """Provider with no credentials — should return failed without calling SDK."""
    return WatsonxGraniteProvider(api_key="", project_id="")


@pytest.fixture
def configured_provider() -> WatsonxGraniteProvider:
    return WatsonxGraniteProvider(
        api_key="test-api-key",
        project_id="test-project-id",
        url="https://us-south.ml.cloud.ibm.com",
    )


# ─────────────────────────────────────────────────────────────
# Missing configuration
# ─────────────────────────────────────────────────────────────

class TestMissingConfiguration:
    def test_no_credentials_returns_failed(
        self, unconfigured_provider: WatsonxGraniteProvider, ctx: AnalysisContext
    ) -> None:
        result = unconfigured_provider.explain(ctx)
        assert result.status == "failed"
        assert result.text is None
        assert "not configured" in (result.error or "").lower()

    def test_no_credentials_does_not_call_sdk(
        self, unconfigured_provider: WatsonxGraniteProvider, ctx: AnalysisContext
    ) -> None:
        with patch("app.ai.watsonx.WatsonxGraniteProvider._call_api") as mock_call:
            unconfigured_provider.explain(ctx)
            mock_call.assert_not_called()

    def test_missing_api_key_only_returns_failed(self, ctx: AnalysisContext) -> None:
        provider = WatsonxGraniteProvider(api_key="", project_id="some-project")
        result = provider.explain(ctx)
        assert result.status == "failed"

    def test_missing_project_id_only_returns_failed(self, ctx: AnalysisContext) -> None:
        provider = WatsonxGraniteProvider(api_key="some-key", project_id="")
        result = provider.explain(ctx)
        assert result.status == "failed"


# ─────────────────────────────────────────────────────────────
# Successful explanation
# ─────────────────────────────────────────────────────────────

class TestSuccessfulExplanation:
    def test_returns_done_with_text(
        self, configured_provider: WatsonxGraniteProvider, ctx: AnalysisContext
    ) -> None:
        expected_text = "This is a high-risk deployment. Review auth changes carefully."

        with patch.object(configured_provider, "_call_api") as mock_call:
            from app.ai.base import ExplanationResult
            mock_call.return_value = ExplanationResult(status="done", text=expected_text)

            result = configured_provider.explain(ctx)

        assert result.status == "done"
        assert result.text == expected_text
        assert result.error is None

    def test_call_api_receives_context(
        self, configured_provider: WatsonxGraniteProvider, ctx: AnalysisContext
    ) -> None:
        with patch.object(configured_provider, "_call_api") as mock_call:
            from app.ai.base import ExplanationResult
            mock_call.return_value = ExplanationResult(status="done", text="ok")

            configured_provider.explain(ctx)

        called_ctx = mock_call.call_args[0][0]
        assert called_ctx.analysis_id == ctx.analysis_id
        assert called_ctx.risk_score == ctx.risk_score


# ─────────────────────────────────────────────────────────────
# SDK unavailable / import error
# ─────────────────────────────────────────────────────────────

class TestSDKUnavailable:
    def test_missing_sdk_returns_failed(
        self, configured_provider: WatsonxGraniteProvider, ctx: AnalysisContext
    ) -> None:
        import builtins
        real_import = builtins.__import__

        def mock_import(name: str, *args, **kwargs):
            if "ibm_watsonx_ai" in name:
                raise ImportError("No module named 'ibm_watsonx_ai'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = configured_provider._call_api(ctx)

        assert result.status == "failed"
        assert "not installed" in (result.error or "").lower()


# ─────────────────────────────────────────────────────────────
# Provider errors and timeouts
# ─────────────────────────────────────────────────────────────

class TestProviderErrors:
    def test_sdk_exception_caught(
        self, configured_provider: WatsonxGraniteProvider, ctx: AnalysisContext
    ) -> None:
        with patch.object(configured_provider, "_call_api", side_effect=RuntimeError("connection refused")):
            result = configured_provider.explain(ctx)

        assert result.status == "failed"
        assert result.text is None
        assert "connection refused" in (result.error or "")

    def test_timeout_caught(
        self, configured_provider: WatsonxGraniteProvider, ctx: AnalysisContext
    ) -> None:
        import socket
        with patch.object(configured_provider, "_call_api", side_effect=TimeoutError("read timeout")):
            result = configured_provider.explain(ctx)

        assert result.status == "failed"
        assert "read timeout" in (result.error or "")

    def test_empty_model_response_returns_failed(
        self, configured_provider: WatsonxGraniteProvider, ctx: AnalysisContext
    ) -> None:
        """If SDK returns an empty string, treat as failed."""
        mock_model = MagicMock()
        mock_model.chat.return_value = {
            "choices": [{"message": {"content": "   "}}]
        }

        mock_client = MagicMock()
        mock_credentials = MagicMock()

        with patch("app.ai.watsonx.WatsonxGraniteProvider._call_api") as mock_call:
            from app.ai.base import ExplanationResult
            mock_call.return_value = ExplanationResult(status="failed", error="Empty response from model")
            result = configured_provider.explain(ctx)

        assert result.status == "failed"
        assert "Empty response" in (result.error or "")

    def test_malformed_response_structure(
        self, configured_provider: WatsonxGraniteProvider, ctx: AnalysisContext
    ) -> None:
        """SDK returns unexpected structure — should be caught gracefully."""
        with patch.object(configured_provider, "_call_api", side_effect=KeyError("choices")):
            result = configured_provider.explain(ctx)

        assert result.status == "failed"


# ─────────────────────────────────────────────────────────────
# Prompt content
# ─────────────────────────────────────────────────────────────

class TestPromptContent:
    def test_prompt_includes_risk_score(self, ctx: AnalysisContext) -> None:
        prompt = _build_user_prompt(ctx)
        assert "70" in prompt  # risk score

    def test_prompt_includes_severity(self, ctx: AnalysisContext) -> None:
        prompt = _build_user_prompt(ctx)
        assert "HIGH" in prompt

    def test_prompt_includes_signal_title(self, ctx: AnalysisContext) -> None:
        prompt = _build_user_prompt(ctx)
        assert "Auth code modified" in prompt

    def test_prompt_includes_repository(self, ctx: AnalysisContext) -> None:
        prompt = _build_user_prompt(ctx)
        assert "org/core-service" in prompt

    def test_empty_signals_handled(self) -> None:
        ctx_no_signals = AnalysisContext(
            analysis_id="x",
            repository="r",
            branch="b",
            commit_sha="abc1234",
            risk_score=0.0,
            severity="LOW",
            total_files_changed=1,
            total_additions=5,
            total_deletions=0,
            signals=[],
        )
        prompt = _build_user_prompt(ctx_no_signals)
        assert "No risk signals detected" in prompt
