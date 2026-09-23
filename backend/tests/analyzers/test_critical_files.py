"""Tests for CriticalFileAnalyzer."""
import pytest

from app.analyzers.critical_files import CriticalFileAnalyzer
from tests.conftest import make_change


@pytest.fixture
def analyzer() -> CriticalFileAnalyzer:
    return CriticalFileAnalyzer()


@pytest.mark.parametrize("path", [
    ".env",
    ".env.production",
    "app/main.py",
    "app/main.ts",
    "app/database.py",
    "alembic.ini",
    "pyproject.toml",
    "tsconfig.json",
    "vite.config.ts",
    "nginx.conf",
])
def test_detects_critical_files(analyzer: CriticalFileAnalyzer, path: str) -> None:
    change = make_change([(path, 5, 2)])
    signals = analyzer.analyze(change)
    assert len(signals) >= 1
    types = {s.signal_type for s in signals}
    assert "CRITICAL_FILE_MODIFIED" in types


def test_no_signal_for_regular_files(analyzer: CriticalFileAnalyzer) -> None:
    change = make_change([
        ("src/services/product.py", 10, 5),
        ("src/models/order.py", 3, 1),
    ])
    assert analyzer.analyze(change) == []


def test_multiple_critical_files_produce_multiple_signals(analyzer: CriticalFileAnalyzer) -> None:
    change = make_change([
        (".env", 1, 0),
        ("app/main.py", 5, 2),
        ("alembic.ini", 1, 0),
    ])
    signals = analyzer.analyze(change)
    assert len(signals) >= 2  # at minimum .env and main.py should both fire


def test_extra_patterns_via_constructor() -> None:
    import re
    custom = CriticalFileAnalyzer(
        extra_patterns=[
            (re.compile(r"very_critical\.py$"), "custom critical file", 25.0),
        ]
    )
    change = make_change([("src/very_critical.py", 3, 0)])
    signals = custom.analyze(change)
    types = {s.signal_type for s in signals}
    assert "CRITICAL_FILE_MODIFIED" in types


def test_evidence_contains_file_type(analyzer: CriticalFileAnalyzer) -> None:
    change = make_change([("nginx.conf", 3, 1)])
    signals = analyzer.analyze(change)
    found = [s for s in signals if s.signal_type == "CRITICAL_FILE_MODIFIED"]
    assert any("nginx" in s.evidence.get("file_type", "") for s in found)
