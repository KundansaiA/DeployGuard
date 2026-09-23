"""Tests for InfrastructureAnalyzer."""
import pytest

from app.analyzers.infrastructure import InfrastructureAnalyzer
from tests.conftest import make_change


@pytest.fixture
def analyzer() -> InfrastructureAnalyzer:
    return InfrastructureAnalyzer()


@pytest.mark.parametrize("path", [
    "Dockerfile",
    "Dockerfile.prod",
    "docker-compose.yml",
    "docker-compose.override.yaml",
    ".dockerignore",
    "kubernetes/backend-deployment.yaml",
    "k8s/service.yaml",
    "helm/values.yaml",
    "backend-deployment.yaml",
    "main.tf",
    "terraform/main.tf",
    "infrastructure/config.yaml",
    "deploy/k8s.yaml",
    ".github/workflows/ci.yml",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    ".circleci/config.yml",
])
def test_detects_infra_files(analyzer: InfrastructureAnalyzer, path: str) -> None:
    change = make_change([(path, 5, 0)])
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    assert signals[0].signal_type == "INFRASTRUCTURE_CHANGE"
    assert signals[0].severity.value == "HIGH"
    assert signals[0].score_contribution == 25.0


def test_no_signal_for_source_files(analyzer: InfrastructureAnalyzer) -> None:
    change = make_change([
        ("src/main.py", 10, 5),
        ("tests/test_app.py", 5, 0),
    ])
    assert analyzer.analyze(change) == []


def test_evidence_lists_infra_files(analyzer: InfrastructureAnalyzer) -> None:
    change = make_change([
        ("Dockerfile", 5, 0),
        ("kubernetes/deployment.yaml", 3, 1),
    ])
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    assert "Dockerfile" in signals[0].evidence["infra_files"]
    assert "kubernetes/deployment.yaml" in signals[0].evidence["infra_files"]
