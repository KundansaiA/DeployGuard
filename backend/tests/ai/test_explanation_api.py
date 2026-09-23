"""API integration tests for explanation endpoints."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.ai.base import ExplanationResult

VALID_PAYLOAD = {
    "repository": "org/my-service",
    "branch": "main",
    "commit_sha": "abc1234",
    "changed_files": [
        {"path": "app/auth/login.py", "additions": 50, "deletions": 10},
    ],
}

EXPLANATION_TEXT = (
    "## Deployment Risk Summary\n"
    "This change modifies authentication code, which is high risk.\n\n"
    "## Key Risk Factors\n"
    "- Auth code changes can introduce security vulnerabilities\n\n"
    "## Recommended Validation Steps\n"
    "1. Run full security test suite\n"
    "2. Review auth flow manually\n\n"
    "## Suggested Testing Areas\n"
    "- Login/logout flows\n"
    "- Session management\n"
)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _create_analysis(client: TestClient) -> str:
    """Create an analysis and return its ID."""
    resp = client.post("/api/v1/analyses", json=VALID_PAYLOAD)
    assert resp.status_code == 201
    return resp.json()["id"]


def _make_provider(status: str = "done", text: str | None = None, error: str | None = None):
    mock = MagicMock()
    mock.explain.return_value = ExplanationResult(status=status, text=text, error=error)  # type: ignore[arg-type]
    return mock


# ─────────────────────────────────────────────────────────────
# GET /explanation — status only (no generation)
# ─────────────────────────────────────────────────────────────

class TestGetExplanation:
    def test_initial_status_is_none(self, client: TestClient) -> None:
        analysis_id = _create_analysis(client)
        resp = client.get(f"/api/v1/analyses/{analysis_id}/explanation")
        assert resp.status_code == 200
        assert resp.json()["status"] == "none"
        assert resp.json()["text"] is None

    def test_404_for_missing_analysis(self, client: TestClient) -> None:
        resp = client.get("/api/v1/analyses/does-not-exist/explanation")
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────
# POST /explanation — trigger generation
# ─────────────────────────────────────────────────────────────

class TestRequestExplanation:
    def test_successful_explanation_returns_done(self, client: TestClient) -> None:
        analysis_id = _create_analysis(client)

        with patch("app.api.v1.routes.analyses.generate_explanation") as mock_gen:
            # Simulate the service updating the analysis and returning it
            from app.models.analysis import Analysis
            from sqlalchemy.orm import Session

            def fake_generate(analysis, db, provider=None):
                analysis.explanation_status = "done"
                analysis.explanation_text = EXPLANATION_TEXT
                db.commit()
                return analysis

            mock_gen.side_effect = fake_generate
            resp = client.post(f"/api/v1/analyses/{analysis_id}/explanation")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert data["text"] == EXPLANATION_TEXT

    def test_provider_unavailable_returns_failed_status(self, client: TestClient) -> None:
        analysis_id = _create_analysis(client)

        with patch("app.api.v1.routes.analyses.generate_explanation") as mock_gen:
            def fake_failed(analysis, db, provider=None):
                analysis.explanation_status = "failed"
                analysis.explanation_text = None
                db.commit()
                return analysis

            mock_gen.side_effect = fake_failed
            resp = client.post(f"/api/v1/analyses/{analysis_id}/explanation")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert data["text"] is None

    def test_404_for_missing_analysis(self, client: TestClient) -> None:
        resp = client.post("/api/v1/analyses/does-not-exist/explanation")
        assert resp.status_code == 404

    def test_cached_explanation_not_regenerated(self, client: TestClient) -> None:
        """Once explanation_status == 'done', POST should return cached result."""
        analysis_id = _create_analysis(client)

        # First call — generates
        with patch("app.api.v1.routes.analyses.generate_explanation") as mock_gen:
            def first_generate(analysis, db, provider=None):
                analysis.explanation_status = "done"
                analysis.explanation_text = "Cached text"
                db.commit()
                return analysis

            mock_gen.side_effect = first_generate
            client.post(f"/api/v1/analyses/{analysis_id}/explanation")
            assert mock_gen.call_count == 1

        # Second call — should use cache (explanation_status == "done")
        with patch("app.api.v1.routes.analyses.generate_explanation") as mock_gen2:
            resp = client.post(f"/api/v1/analyses/{analysis_id}/explanation")
            mock_gen2.assert_not_called()

        assert resp.json()["status"] == "done"
        assert resp.json()["text"] == "Cached text"

    def test_explanation_does_not_alter_risk_score(self, client: TestClient) -> None:
        """The deterministic score must be unchanged after explanation generation."""
        analysis_id = _create_analysis(client)
        original_score = client.get(f"/api/v1/analyses/{analysis_id}").json()["risk_score"]

        with patch("app.api.v1.routes.analyses.generate_explanation") as mock_gen:
            def fake_generate(analysis, db, provider=None):
                analysis.explanation_status = "done"
                analysis.explanation_text = "Some text"
                db.commit()
                return analysis

            mock_gen.side_effect = fake_generate
            client.post(f"/api/v1/analyses/{analysis_id}/explanation")

        score_after = client.get(f"/api/v1/analyses/{analysis_id}").json()["risk_score"]
        assert original_score == score_after

    def test_analysis_still_returns_after_failed_explanation(self, client: TestClient) -> None:
        """Deterministic result must be accessible even when explanation fails."""
        analysis_id = _create_analysis(client)

        with patch("app.api.v1.routes.analyses.generate_explanation") as mock_gen:
            def fake_failed(analysis, db, provider=None):
                analysis.explanation_status = "failed"
                analysis.explanation_text = None
                db.commit()
                return analysis

            mock_gen.side_effect = fake_failed
            client.post(f"/api/v1/analyses/{analysis_id}/explanation")

        # The analysis itself must still be fully accessible
        resp = client.get(f"/api/v1/analyses/{analysis_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_score"] is not None
        assert data["severity"] is not None
