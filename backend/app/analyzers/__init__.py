"""Analyzers package — exports the registry of all active analyzers."""
from app.analyzers.auth_security import AuthSecurityAnalyzer
from app.analyzers.base import Analyzer, RiskSignal, SignalSeverity
from app.analyzers.change_size import ChangeSizeAnalyzer
from app.analyzers.critical_files import CriticalFileAnalyzer
from app.analyzers.database_migration import DatabaseMigrationAnalyzer
from app.analyzers.dependency import DependencyAnalyzer
from app.analyzers.infrastructure import InfrastructureAnalyzer
from app.analyzers.test_coverage import TestCoverageAnalyzer

__all__ = [
    "Analyzer",
    "RiskSignal",
    "SignalSeverity",
    "AuthSecurityAnalyzer",
    "ChangeSizeAnalyzer",
    "CriticalFileAnalyzer",
    "DatabaseMigrationAnalyzer",
    "DependencyAnalyzer",
    "InfrastructureAnalyzer",
    "TestCoverageAnalyzer",
    "build_analyzer_registry",
]


def build_analyzer_registry() -> list[Analyzer]:
    """Return the ordered list of all active analyzers.

    This is the single place where analyzers are registered.
    Add new analyzers here to include them in the pipeline.
    """
    return [
        ChangeSizeAnalyzer(),
        DatabaseMigrationAnalyzer(),
        AuthSecurityAnalyzer(),
        InfrastructureAnalyzer(),
        TestCoverageAnalyzer(),
        DependencyAnalyzer(),
        CriticalFileAnalyzer(),
    ]
