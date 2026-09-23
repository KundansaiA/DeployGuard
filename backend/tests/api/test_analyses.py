"""API integration tests for POST/GET /api/v1/analyses."""
import pytest
from fastapi.testclient import TestClient


VALID_PAYLOAD = {
    "repository": "org/my-service",
    "branch": "feature/payment-refactor",
    "commit_sha": "abc1234def567890",
    "changed_files": [
        {"path": "src/services/payment.py", "additions": 80, "deletions": 20},
        {"path": "tests/test_payment.py", "additions": 40, "deletions": 5},
    ],
}


class TestCreateAnalysis:
    def test_successful_submission_returns_201(self, client: TestClient) -> None:
        response = client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        assert response.status_code == 201

    def test_response_contains_id(self, client: TestClient) -> None:
        response = client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        data = response.json()
        assert "id" in data
        assert len(data["id"]) == 36  # UUID format

    def test_response_contains_score_and_severity(self, client: TestClient) -> None:
        response = client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        data = response.json()
        assert "risk_score" in data
        assert "severity" in data
        assert data["severity"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    def test_response_score_within_bounds(self, client: TestClient) -> None:
        response = client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        data = response.json()
        assert 0.0 <= data["risk_score"] <= 100.0

    def test_response_contains_signals(self, client: TestClient) -> None:
        response = client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        data = response.json()
        assert "signals" in data
        assert isinstance(data["signals"], list)

    def test_signal_fields_present(self, client: TestClient) -> None:
        response = client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        data = response.json()
        if data["signals"]:
            signal = data["signals"][0]
            for field in ("id", "signal_type", "severity", "title", "description", "score_contribution", "source_analyzer"):
                assert field in signal

    def test_echo_of_input_fields(self, client: TestClient) -> None:
        response = client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        data = response.json()
        assert data["repository"] == VALID_PAYLOAD["repository"]
        assert data["branch"] == VALID_PAYLOAD["branch"]
        assert data["commit_sha"] == VALID_PAYLOAD["commit_sha"].lower()

    def test_explanation_text_is_null(self, client: TestClient) -> None:
        """Granite is not called in tests — explanation should be null."""
        response = client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        assert response.json()["explanation_text"] is None

    def test_empty_changed_files_returns_zero_score(self, client: TestClient) -> None:
        payload = {**VALID_PAYLOAD, "changed_files": []}
        response = client.post("/api/v1/analyses", json=payload)
        assert response.status_code == 201
        assert response.json()["risk_score"] == 0.0
        assert response.json()["severity"] == "LOW"

    def test_high_risk_change_raises_score(self, client: TestClient) -> None:
        """Auth + DB migration + large change should produce a HIGH/CRITICAL score."""
        payload = {
            "repository": "org/core",
            "branch": "main",
            "commit_sha": "deadbeef",
            "changed_files": [
                {"path": "app/auth/login.py", "additions": 200, "deletions": 50},
                {"path": "alembic/versions/001_drop_table.py", "additions": 30, "deletions": 0},
                *[{"path": f"src/module_{i}.py", "additions": 20, "deletions": 5} for i in range(30)],
            ],
        }
        response = client.post("/api/v1/analyses", json=payload)
        data = response.json()
        assert data["risk_score"] >= 50.0
        assert data["severity"] in {"HIGH", "CRITICAL"}

    def test_missing_required_field_returns_422(self, client: TestClient) -> None:
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "repository"}
        response = client.post("/api/v1/analyses", json=payload)
        assert response.status_code == 422

    def test_invalid_commit_sha_returns_422(self, client: TestClient) -> None:
        payload = {**VALID_PAYLOAD, "commit_sha": "not-a-hex-string!!"}
        response = client.post("/api/v1/analyses", json=payload)
        assert response.status_code == 422

    def test_negative_additions_returns_422(self, client: TestClient) -> None:
        payload = {
            **VALID_PAYLOAD,
            "changed_files": [{"path": "src/foo.py", "additions": -1, "deletions": 0}],
        }
        response = client.post("/api/v1/analyses", json=payload)
        assert response.status_code == 422

    def test_short_commit_sha_accepted(self, client: TestClient) -> None:
        payload = {**VALID_PAYLOAD, "commit_sha": "abc1234"}
        response = client.post("/api/v1/analyses", json=payload)
        assert response.status_code == 201


class TestGetAnalysis:
    def test_get_existing_analysis(self, client: TestClient) -> None:
        created = client.post("/api/v1/analyses", json=VALID_PAYLOAD).json()
        response = client.get(f"/api/v1/analyses/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_nonexistent_returns_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/analyses/does-not-exist")
        assert response.status_code == 404

    def test_retrieved_analysis_matches_created(self, client: TestClient) -> None:
        created = client.post("/api/v1/analyses", json=VALID_PAYLOAD).json()
        retrieved = client.get(f"/api/v1/analyses/{created['id']}").json()
        assert retrieved["risk_score"] == created["risk_score"]
        assert retrieved["severity"] == created["severity"]
        assert len(retrieved["signals"]) == len(created["signals"])


class TestListAnalyses:
    def test_empty_list_initially(self, client: TestClient) -> None:
        response = client.get("/api/v1/analyses")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_contains_created_analysis(self, client: TestClient) -> None:
        client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        response = client.get("/api/v1/analyses")
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_pagination_skip(self, client: TestClient) -> None:
        for _ in range(3):
            client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        response = client.get("/api/v1/analyses?skip=2&limit=10")
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 1

    def test_pagination_limit(self, client: TestClient) -> None:
        for _ in range(5):
            client.post("/api/v1/analyses", json=VALID_PAYLOAD)
        response = client.get("/api/v1/analyses?limit=2")
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_invalid_limit_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/v1/analyses?limit=0")
        assert response.status_code == 422

    def test_invalid_skip_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/v1/analyses?skip=-1")
        assert response.status_code == 422
