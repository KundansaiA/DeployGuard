"""Tests for DependencyAnalyzer."""
import pytest

from app.analyzers.dependency import DependencyAnalyzer
from tests.conftest import make_change


@pytest.fixture
def analyzer() -> DependencyAnalyzer:
    return DependencyAnalyzer()


@pytest.mark.parametrize("lockfile", [
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
    "go.sum",
    "Gemfile.lock",
    "composer.lock",
])
def test_detects_lockfile_changes(analyzer: DependencyAnalyzer, lockfile: str) -> None:
    change = make_change([(lockfile, 50, 30)])
    signals = analyzer.analyze(change)
    types = {s.signal_type for s in signals}
    assert "LOCKFILE_CHANGED" in types
    lockfile_signal = next(s for s in signals if s.signal_type == "LOCKFILE_CHANGED")
    assert lockfile_signal.severity.value == "MEDIUM"
    assert lockfile_signal.score_contribution == 15.0


@pytest.mark.parametrize("manifest", [
    "package.json",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "setup.py",
    "Pipfile",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
])
def test_detects_manifest_changes(analyzer: DependencyAnalyzer, manifest: str) -> None:
    change = make_change([(manifest, 3, 1)])
    signals = analyzer.analyze(change)
    types = {s.signal_type for s in signals}
    assert "DEPENDENCY_MANIFEST_CHANGED" in types


def test_both_signals_when_lockfile_and_manifest_changed(analyzer: DependencyAnalyzer) -> None:
    change = make_change([
        ("package.json", 2, 0),
        ("package-lock.json", 100, 80),
    ])
    signals = analyzer.analyze(change)
    types = {s.signal_type for s in signals}
    assert "LOCKFILE_CHANGED" in types
    assert "DEPENDENCY_MANIFEST_CHANGED" in types


def test_no_signal_for_source_files(analyzer: DependencyAnalyzer) -> None:
    change = make_change([
        ("src/app.py", 10, 5),
        ("src/utils.py", 3, 1),
    ])
    assert analyzer.analyze(change) == []
