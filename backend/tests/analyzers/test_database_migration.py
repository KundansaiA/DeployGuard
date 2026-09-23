"""Tests for DatabaseMigrationAnalyzer."""
import pytest

from app.analyzers.database_migration import DatabaseMigrationAnalyzer
from tests.conftest import make_change


@pytest.fixture
def analyzer() -> DatabaseMigrationAnalyzer:
    return DatabaseMigrationAnalyzer()


@pytest.mark.parametrize("path", [
    "alembic/versions/001_add_users.py",
    "db/migrations/20240101_create_table.sql",
    "migrations/add_column.py",
    "schema.sql",
    "schema.rb",
    "flyway/V1__init.sql",
    "liquibase/changelog.sql",
    "app/db/migrate/001.sql",
])
def test_detects_migration_files(analyzer: DatabaseMigrationAnalyzer, path: str) -> None:
    change = make_change([(path, 10, 0)])
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    assert signals[0].signal_type == "DATABASE_MIGRATION"
    assert signals[0].severity.value == "HIGH"
    assert signals[0].score_contribution == 30.0


def test_no_signal_for_non_migration_files(analyzer: DatabaseMigrationAnalyzer) -> None:
    change = make_change([
        ("src/models/user.py", 10, 5),
        ("src/api/routes.py", 3, 1),
    ])
    assert analyzer.analyze(change) == []


def test_evidence_contains_file_paths(analyzer: DatabaseMigrationAnalyzer) -> None:
    change = make_change([
        ("alembic/versions/001.py", 5, 0),
        ("alembic/versions/002.py", 3, 0),
    ])
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    ev = signals[0].evidence
    assert "alembic/versions/001.py" in ev["migration_files"]
    assert "alembic/versions/002.py" in ev["migration_files"]


def test_mixed_files_only_migration_flagged(analyzer: DatabaseMigrationAnalyzer) -> None:
    change = make_change([
        ("src/models/user.py", 5, 0),
        ("alembic/versions/003_add_index.py", 10, 0),
    ])
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    assert "alembic/versions/003_add_index.py" in signals[0].evidence["migration_files"]
    assert "src/models/user.py" not in signals[0].evidence["migration_files"]
