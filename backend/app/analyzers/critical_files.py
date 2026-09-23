"""Critical File Analyzer.

Detects modifications to configurable high-risk file paths. The default
set covers common high-impact configuration and entry-point files.

The list can be extended via constructor injection for project-specific
critical paths.
"""
import re

from app.analyzers.base import Analyzer, RiskSignal, SignalSeverity
from app.ingestion.types import ChangePayload

_NAME = "CriticalFileAnalyzer"

# Default high-risk paths/patterns. Each entry is (pattern, label, score).
_DEFAULT_CRITICAL_PATTERNS: list[tuple[re.Pattern[str], str, float]] = [
    # Environment and secrets
    (re.compile(r"(^|/)\.env(\.[a-z]+)?$", re.IGNORECASE), "environment config", 30.0),
    (re.compile(r"(^|/)secrets?(\.[a-z]+)?$", re.IGNORECASE), "secrets file", 35.0),
    # Application entry points
    (re.compile(r"(^|/)main\.(py|go|ts|js|rs)$", re.IGNORECASE), "application entry point", 20.0),
    (re.compile(r"(^|/)app\.(py|go|ts|js|rs)$", re.IGNORECASE), "application entry point", 20.0),
    (re.compile(r"(^|/)wsgi\.py$", re.IGNORECASE), "WSGI entry point", 20.0),
    (re.compile(r"(^|/)asgi\.py$", re.IGNORECASE), "ASGI entry point", 20.0),
    # Database configuration
    (re.compile(r"(^|/)database\.(py|ts|js)$", re.IGNORECASE), "database config", 20.0),
    (re.compile(r"(^|/)alembic\.ini$", re.IGNORECASE), "Alembic config", 15.0),
    # Build and project config
    (re.compile(r"(^|/)pyproject\.toml$", re.IGNORECASE), "Python project config", 10.0),
    (re.compile(r"(^|/)setup\.py$", re.IGNORECASE), "Python setup", 10.0),
    (re.compile(r"(^|/)tsconfig(\..*)?\.json$", re.IGNORECASE), "TypeScript config", 10.0),
    (re.compile(r"(^|/)vite\.config\.(ts|js)$", re.IGNORECASE), "Vite build config", 10.0),
    (re.compile(r"(^|/)webpack\.config\.(ts|js)$", re.IGNORECASE), "webpack build config", 10.0),
    # Security configs
    (re.compile(r"(^|/)nginx\.conf$", re.IGNORECASE), "nginx config", 20.0),
    (re.compile(r"(^|/)apache.*\.conf$", re.IGNORECASE), "Apache config", 20.0),
    (re.compile(r"(^|/)cors\.(py|ts|js)$", re.IGNORECASE), "CORS config", 20.0),
]


class CriticalFileAnalyzer:
    """Flags modifications to known high-risk files."""

    def __init__(
        self,
        extra_patterns: list[tuple[re.Pattern[str], str, float]] | None = None,
    ) -> None:
        self._patterns = list(_DEFAULT_CRITICAL_PATTERNS)
        if extra_patterns:
            self._patterns.extend(extra_patterns)

    def analyze(self, change: ChangePayload) -> list[RiskSignal]:
        signals: list[RiskSignal] = []

        for pattern, label, score in self._patterns:
            matched = [f for f in change.changed_files if pattern.search(f.path)]
            if matched:
                paths = [f.path for f in matched]
                signals.append(
                    RiskSignal(
                        signal_type="CRITICAL_FILE_MODIFIED",
                        severity=SignalSeverity.HIGH if score >= 20.0 else SignalSeverity.MEDIUM,
                        title=f"Critical file modified: {label}",
                        description=(
                            f"A high-risk file ({label}) was modified: {', '.join(paths)}. "
                            "Changes to critical configuration or entry-point files can have "
                            "wide-ranging effects on system behavior. Review carefully before deploying."
                        ),
                        score_contribution=score,
                        source_analyzer=_NAME,
                        evidence={"critical_files": paths, "file_type": label},
                    )
                )

        return signals


_: Analyzer = CriticalFileAnalyzer()
