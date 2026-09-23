"""Database Migration Analyzer.

Detects changes that touch database migration files or schema definitions.
Migration deployments carry elevated risk due to potential data loss or
irreversible schema changes.
"""
import re

from app.analyzers.base import Analyzer, RiskSignal, SignalSeverity
from app.ingestion.types import ChangePayload

_NAME = "DatabaseMigrationAnalyzer"

# Path fragments that strongly indicate a migration file
_MIGRATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(^|/)migrations?/", re.IGNORECASE),
    re.compile(r"(^|/)alembic/versions/", re.IGNORECASE),
    re.compile(r"(^|/)db/migrate/", re.IGNORECASE),
    re.compile(r"(^|/)schema\.(rb|sql|py)$", re.IGNORECASE),
    re.compile(r"(^|/)flyway/", re.IGNORECASE),
    re.compile(r"(^|/)liquibase/", re.IGNORECASE),
    re.compile(r"\.(sql)$", re.IGNORECASE),
]


def _is_migration_file(path: str) -> bool:
    return any(p.search(path) for p in _MIGRATION_PATTERNS)


class DatabaseMigrationAnalyzer:
    """Flags changes that include database migration or schema files."""

    def analyze(self, change: ChangePayload) -> list[RiskSignal]:
        migration_files = [f for f in change.changed_files if _is_migration_file(f.path)]
        if not migration_files:
            return []

        paths = [f.path for f in migration_files]
        return [
            RiskSignal(
                signal_type="DATABASE_MIGRATION",
                severity=SignalSeverity.HIGH,
                title=f"Database migration detected ({len(migration_files)} file(s))",
                description=(
                    "This change includes database migration or schema files. "
                    "Migrations may alter table structure, drop columns, or modify indexes. "
                    "Ensure migrations are backward-compatible and have been tested against "
                    "a production-like dataset before deploying."
                ),
                score_contribution=30.0,
                source_analyzer=_NAME,
                evidence={"migration_files": paths},
            )
        ]


_: Analyzer = DatabaseMigrationAnalyzer()
