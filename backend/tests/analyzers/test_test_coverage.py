"""Tests for TestCoverageAnalyzer."""
import pytest

from app.analyzers.test_coverage import TestCoverageAnalyzer
from tests.conftest import make_change


@pytest.fixture
def analyzer() -> TestCoverageAnalyzer:
    return TestCoverageAnalyzer()


def test_no_signal_when_tests_accompany_changes(analyzer: TestCoverageAnalyzer) -> None:
    change = make_change([
        ("src/services/payment.py", 20, 5),
        ("tests/test_payment.py", 15, 0),
    ])
    assert analyzer.analyze(change) == []


def test_no_test_changes_signal(analyzer: TestCoverageAnalyzer) -> None:
    change = make_change([
        ("src/services/payment.py", 20, 5),
        ("src/models/order.py", 10, 2),
    ])
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    assert signals[0].signal_type == "NO_TEST_CHANGES"
    assert signals[0].severity.value == "MEDIUM"
    assert signals[0].score_contribution == 20.0


def test_low_ratio_signal(analyzer: TestCoverageAnalyzer) -> None:
    # 5 prod files, 1 test file → ratio 0.2 < 0.25 threshold
    prod_files = [(f"src/module_{i}.py", 10, 0) for i in range(5)]
    test_file = [("tests/test_module_0.py", 5, 0)]
    change = make_change(prod_files + test_file)
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    assert signals[0].signal_type == "LOW_TEST_COVERAGE_RATIO"
    assert signals[0].severity.value == "LOW"


def test_no_signal_for_non_prod_only_changes(analyzer: TestCoverageAnalyzer) -> None:
    # Only config / docs files — no signal expected
    change = make_change([
        ("README.md", 5, 0),
        ("requirements.txt", 1, 0),
        ("pyproject.toml", 2, 1),
    ])
    assert analyzer.analyze(change) == []


def test_no_signal_for_test_only_changes(analyzer: TestCoverageAnalyzer) -> None:
    change = make_change([
        ("tests/test_something.py", 20, 5),
    ])
    assert analyzer.analyze(change) == []


def test_evidence_contains_file_lists(analyzer: TestCoverageAnalyzer) -> None:
    change = make_change([
        ("src/services/billing.py", 30, 10),
    ])
    signals = analyzer.analyze(change)
    ev = signals[0].evidence
    assert "src/services/billing.py" in ev["production_files"]
    assert ev["test_file_count"] == 0
    assert ev["production_file_count"] == 1


@pytest.mark.parametrize("test_path", [
    "tests/test_foo.py",
    "src/__tests__/foo.test.ts",
    "src/foo.spec.ts",
    "spec/foo_spec.rb",
    "conftest.py",
])
def test_recognizes_test_files(analyzer: TestCoverageAnalyzer, test_path: str) -> None:
    change = make_change([
        ("src/foo.py", 10, 0),
        (test_path, 5, 0),
    ])
    # With a test file, should either produce no signal or a ratio signal
    signals = analyzer.analyze(change)
    types = [s.signal_type for s in signals]
    assert "NO_TEST_CHANGES" not in types
