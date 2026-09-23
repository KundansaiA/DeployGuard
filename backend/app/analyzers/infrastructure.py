"""Infrastructure Analyzer.

Detects changes involving Docker, Kubernetes, deployment manifests,
infrastructure-as-code, or CI/CD workflows. Infrastructure changes
affect the deployment environment itself and carry elevated risk.
"""
import re

from app.analyzers.base import Analyzer, RiskSignal, SignalSeverity
from app.ingestion.types import ChangePayload

_NAME = "InfrastructureAnalyzer"

_INFRA_PATH_PATTERNS: list[re.Pattern[str]] = [
    # Docker
    re.compile(r"(^|/)Dockerfile(\.[a-z]+)?$", re.IGNORECASE),
    re.compile(r"(^|/)docker-compose(\.[a-z]+)?\.ya?ml$", re.IGNORECASE),
    re.compile(r"(^|/)\.dockerignore$", re.IGNORECASE),
    # Kubernetes
    re.compile(r"(^|/)kubernetes/", re.IGNORECASE),
    re.compile(r"(^|/)k8s/", re.IGNORECASE),
    re.compile(r"(^|/)helm/", re.IGNORECASE),
    re.compile(r"(deployment|statefulset|daemonset|ingress|service)\.ya?ml$", re.IGNORECASE),
    # Terraform / Pulumi / CDK
    re.compile(r"\.tf(vars)?$", re.IGNORECASE),
    re.compile(r"(^|/)terraform/", re.IGNORECASE),
    re.compile(r"(^|/)pulumi/", re.IGNORECASE),
    re.compile(r"(^|/)cdk\.json$", re.IGNORECASE),
    # CI/CD
    re.compile(r"(^|/)\.github/workflows/", re.IGNORECASE),
    re.compile(r"(^|/)\.gitlab-ci\.ya?ml$", re.IGNORECASE),
    re.compile(r"(^|/)Jenkinsfile$", re.IGNORECASE),
    re.compile(r"(^|/)\.circleci/", re.IGNORECASE),
    # Generic infra / config
    re.compile(r"(^|/)infrastructure/", re.IGNORECASE),
    re.compile(r"(^|/)deploy/", re.IGNORECASE),
    re.compile(r"(^|/)ansible/", re.IGNORECASE),
]


def _is_infra_file(path: str) -> bool:
    return any(p.search(path) for p in _INFRA_PATH_PATTERNS)


def _classify_infra_type(paths: list[str]) -> str:
    """Return a human-readable summary of the infra types touched."""
    labels: set[str] = set()
    for path in paths:
        if re.search(r"Dockerfile|docker-compose|\.dockerignore", path, re.IGNORECASE):
            labels.add("Docker")
        if re.search(r"kubernetes|k8s|helm|deployment\.ya?ml", path, re.IGNORECASE):
            labels.add("Kubernetes")
        if re.search(r"\.tf|terraform|pulumi|cdk", path, re.IGNORECASE):
            labels.add("IaC")
        if re.search(r"\.github/workflows|gitlab-ci|Jenkinsfile|circleci", path, re.IGNORECASE):
            labels.add("CI/CD")
        if re.search(r"infrastructure|deploy|ansible", path, re.IGNORECASE):
            labels.add("Infrastructure config")
    return ", ".join(sorted(labels)) if labels else "infrastructure"


class InfrastructureAnalyzer:
    """Flags changes to infrastructure, containerization, or CI/CD configuration."""

    def analyze(self, change: ChangePayload) -> list[RiskSignal]:
        infra_files = [f for f in change.changed_files if _is_infra_file(f.path)]
        if not infra_files:
            return []

        paths = [f.path for f in infra_files]
        infra_type = _classify_infra_type(paths)

        return [
            RiskSignal(
                signal_type="INFRASTRUCTURE_CHANGE",
                severity=SignalSeverity.HIGH,
                title=f"Infrastructure configuration modified ({infra_type})",
                description=(
                    f"This change modifies infrastructure or deployment configuration ({infra_type}). "
                    "Changes to Dockerfiles, Kubernetes manifests, or CI/CD pipelines directly "
                    "affect how the application is built and deployed. "
                    "Verify changes in a staging environment before production deployment."
                ),
                score_contribution=25.0,
                source_analyzer=_NAME,
                evidence={"infra_files": paths, "infra_types": infra_type},
            )
        ]


_: Analyzer = InfrastructureAnalyzer()
