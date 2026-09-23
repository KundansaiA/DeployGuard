"""Dependency Analyzer.

Detects changes to dependency manifests and lockfiles. Dependency changes
may introduce supply-chain risks, breaking API changes, or security vulnerabilities.
"""
import re

from app.analyzers.base import Analyzer, RiskSignal, SignalSeverity
from app.ingestion.types import ChangePayload

_NAME = "DependencyAnalyzer"

# Lockfiles carry higher risk than manifest-only changes
_LOCKFILE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(^|/)package-lock\.json$", re.IGNORECASE),
    re.compile(r"(^|/)yarn\.lock$", re.IGNORECASE),
    re.compile(r"(^|/)pnpm-lock\.yaml$", re.IGNORECASE),
    re.compile(r"(^|/)poetry\.lock$", re.IGNORECASE),
    re.compile(r"(^|/)Pipfile\.lock$", re.IGNORECASE),
    re.compile(r"(^|/)Cargo\.lock$", re.IGNORECASE),
    re.compile(r"(^|/)go\.sum$", re.IGNORECASE),
    re.compile(r"(^|/)Gemfile\.lock$", re.IGNORECASE),
    re.compile(r"(^|/)composer\.lock$", re.IGNORECASE),
]

_MANIFEST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(^|/)package\.json$", re.IGNORECASE),
    re.compile(r"(^|/)requirements[\w.-]*\.txt$", re.IGNORECASE),
    re.compile(r"(^|/)pyproject\.toml$", re.IGNORECASE),
    re.compile(r"(^|/)setup\.(py|cfg)$", re.IGNORECASE),
    re.compile(r"(^|/)Pipfile$", re.IGNORECASE),
    re.compile(r"(^|/)Cargo\.toml$", re.IGNORECASE),
    re.compile(r"(^|/)go\.mod$", re.IGNORECASE),
    re.compile(r"(^|/)Gemfile$", re.IGNORECASE),
    re.compile(r"(^|/)composer\.json$", re.IGNORECASE),
    re.compile(r"(^|/)build\.gradle(\.kts)?$", re.IGNORECASE),
    re.compile(r"(^|/)pom\.xml$", re.IGNORECASE),
    re.compile(r"(^|/)\.csproj$", re.IGNORECASE),
]


def _is_lockfile(path: str) -> bool:
    return any(p.search(path) for p in _LOCKFILE_PATTERNS)


def _is_manifest(path: str) -> bool:
    return any(p.search(path) for p in _MANIFEST_PATTERNS)


class DependencyAnalyzer:
    """Flags changes to dependency manifests and lockfiles."""

    def analyze(self, change: ChangePayload) -> list[RiskSignal]:
        lockfiles = [f for f in change.changed_files if _is_lockfile(f.path)]
        manifests = [f for f in change.changed_files if _is_manifest(f.path) and not _is_lockfile(f.path)]

        signals: list[RiskSignal] = []

        if lockfiles:
            lock_paths = [f.path for f in lockfiles]
            signals.append(
                RiskSignal(
                    signal_type="LOCKFILE_CHANGED",
                    severity=SignalSeverity.MEDIUM,
                    title=f"Dependency lockfile(s) changed ({len(lockfiles)} file(s))",
                    description=(
                        "One or more dependency lockfiles were modified. "
                        "Lockfile changes indicate concrete dependency version changes that "
                        "may introduce breaking changes, supply-chain risks, or new vulnerabilities. "
                        "Review the diff carefully for unexpected dependency version bumps."
                    ),
                    score_contribution=15.0,
                    source_analyzer=_NAME,
                    evidence={"lockfiles": lock_paths},
                )
            )

        if manifests:
            manifest_paths = [f.path for f in manifests]
            signals.append(
                RiskSignal(
                    signal_type="DEPENDENCY_MANIFEST_CHANGED",
                    severity=SignalSeverity.LOW,
                    title=f"Dependency manifest(s) changed ({len(manifests)} file(s))",
                    description=(
                        "One or more dependency manifest files were modified without a corresponding "
                        "lockfile update, or independently of a lockfile. "
                        "Ensure the correct dependency versions will be resolved at build time."
                    ),
                    score_contribution=8.0,
                    source_analyzer=_NAME,
                    evidence={"manifests": manifest_paths},
                )
            )

        return signals


_: Analyzer = DependencyAnalyzer()
