"""Tests for ChangeSizeAnalyzer."""
import pytest

from app.analyzers.change_size import ChangeSizeAnalyzer
from tests.conftest import make_change


@pytest.fixture
def analyzer() -> ChangeSizeAnalyzer:
    return ChangeSizeAnalyzer()


def test_no_signal_for_small_change(analyzer: ChangeSizeAnalyzer) -> None:
    change = make_change([
        ("src/app.py", 5, 2),
        ("src/utils.py", 3, 1),
    ])
    assert analyzer.analyze(change) == []


def test_medium_signal_on_file_threshold(analyzer: ChangeSizeAnalyzer) -> None:
    # 11 files, tiny line count — should hit file threshold for MEDIUM
    files = [(f"src/file_{i}.py", 1, 1) for i in range(11)]
    change = make_change(files)
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    assert signals[0].signal_type == "LARGE_CHANGE"
    assert signals[0].severity.value == "MEDIUM"


def test_medium_signal_on_line_threshold(analyzer: ChangeSizeAnalyzer) -> None:
    # 2 files but >300 line changes
    change = make_change([("src/big.py", 200, 150)])
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    assert signals[0].severity.value == "MEDIUM"


def test_high_signal_on_file_threshold(analyzer: ChangeSizeAnalyzer) -> None:
    files = [(f"src/file_{i}.py", 1, 1) for i in range(26)]
    change = make_change(files)
    signals = analyzer.analyze(change)
    assert signals[0].severity.value == "HIGH"


def test_high_signal_on_line_threshold(analyzer: ChangeSizeAnalyzer) -> None:
    change = make_change([("src/huge.py", 500, 350)])
    signals = analyzer.analyze(change)
    assert signals[0].severity.value == "HIGH"


def test_critical_signal_on_file_threshold(analyzer: ChangeSizeAnalyzer) -> None:
    files = [(f"src/file_{i}.py", 1, 1) for i in range(51)]
    change = make_change(files)
    signals = analyzer.analyze(change)
    assert signals[0].severity.value == "CRITICAL"
    assert signals[0].score_contribution == 40.0


def test_critical_signal_on_line_threshold(analyzer: ChangeSizeAnalyzer) -> None:
    change = make_change([("src/monster.py", 1500, 600)])
    signals = analyzer.analyze(change)
    assert signals[0].severity.value == "CRITICAL"


def test_evidence_fields(analyzer: ChangeSizeAnalyzer) -> None:
    change = make_change([("src/big.py", 200, 150)])
    signals = analyzer.analyze(change)
    ev = signals[0].evidence
    assert ev["files_changed"] == 1
    assert ev["total_additions"] == 200
    assert ev["total_deletions"] == 150
    assert ev["total_line_changes"] == 350


def test_empty_change_no_signal(analyzer: ChangeSizeAnalyzer) -> None:
    change = make_change([])
    assert analyzer.analyze(change) == []
