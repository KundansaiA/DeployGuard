"""Test Coverage Analyzer.

Detects situations where production code changes without corresponding
test file changes, which may indicate the change is untested.

Logic:
- Count production source files changed (non-test, non-config).
- Count test files changed.
- If production files are changed but zero test files are changed,
  emit a risk signal.
- If the ratio of test files to production files is below a threshold,
  emit a lower-severity signal.
"""
import re

from app.analyzers.base import Analyzer, RiskSignal, SignalSeverity
from app.ingestion.types import ChangePayload

_NAME = "TestCoverageAnalyzer"

_TEST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(^|[/_-])test[s]?[/_.-]", re.IGNORECASE),
    re.compile(r"[/_.-]test[s]?\.(py|ts|tsx|js|jsx|go|java|rb|cs)$", re.IGNORECASE),
    re.compile(r"[/_.-]spec\.(py|ts|tsx|js|jsx|go|java|rb|cs)$", re.IGNORECASE),
    re.compile(r"(^|/)__tests__/", re.IGNORECASE),
    re.compile(r"(^|/)spec/", re.IGNORECASE),
    re.compile(r"conftest\.py$", re.IGNORECASE),
]

# Extensions considered "production source code"
_PROD_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".go", ".java", ".rb", ".cs", ".rs", ".swift", ".kt",
}

# Paths that are NOT production code (configs, docs, generated, etc.)
_NON_PROD_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.(md|txt|rst|json|yaml|yml|toml|cfg|ini|lock|sum)$", re.IGNORECASE),
    re.compile(r"(^|/)docs?/", re.IGNORECASE),
    re.compile(r"(^|/)\.github/", re.IGNORECASE),
    re.compile(r"(^|/)migrations?/", re.IGNORECASE),
]


def _is_test_file(path: str) -> bool:
    return any(p.search(path) for p in _TEST_PATTERNS)


def _is_prod_file(path: str) -> bool:
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext not in _PROD_EXTENSIONS:
        return False
    if _is_test_file(path):
        return False
    if any(p.search(path) for p in _NON_PROD_PATTERNS):
        return False
    return True


class TestCoverageAnalyzer:
    """Flags production code changes that lack accompanying test changes."""

    # Minimum ratio of test files changed per production file changed
    _MIN_TEST_RATIO = 0.25

    def analyze(self, change: ChangePayload) -> list[RiskSignal]:
        prod_files = [f for f in change.changed_files if _is_prod_file(f.path)]
        test_files = [f for f in change.changed_files if _is_test_file(f.path)]

        if not prod_files:
            # No production code changed — no signal
            return []

        prod_paths = [f.path for f in prod_files]
        test_paths = [f.path for f in test_files]

        if not test_files:
            return [
                RiskSignal(
                    signal_type="NO_TEST_CHANGES",
                    severity=SignalSeverity.MEDIUM,
                    title=f"{len(prod_files)} production file(s) changed with no test changes",
                    description=(
                        "Production source code was modified but no test files were changed. "
                        "This may indicate the change is untested, increasing the risk of "
                        "undetected regressions in production."
                    ),
                    score_contribution=20.0,
                    source_analyzer=_NAME,
                    evidence={
                        "production_files": prod_paths,
                        "test_files": test_paths,
                        "production_file_count": len(prod_files),
                        "test_file_count": 0,
                    },
                )
            ]

        ratio = len(test_files) / len(prod_files)
        if ratio < self._MIN_TEST_RATIO:
            return [
                RiskSignal(
                    signal_type="LOW_TEST_COVERAGE_RATIO",
                    severity=SignalSeverity.LOW,
                    title="Low test-to-production change ratio",
                    description=(
                        f"{len(prod_files)} production file(s) changed but only "
                        f"{len(test_files)} test file(s) changed "
                        f"(ratio: {ratio:.2f}, minimum: {self._MIN_TEST_RATIO}). "
                        "Consider adding or updating tests to cover the new changes."
                    ),
                    score_contribution=10.0,
                    source_analyzer=_NAME,
                    evidence={
                        "production_files": prod_paths,
                        "test_files": test_paths,
                        "production_file_count": len(prod_files),
                        "test_file_count": len(test_files),
                        "ratio": round(ratio, 4),
                    },
                )
            ]

        return []


_: Analyzer = TestCoverageAnalyzer()
