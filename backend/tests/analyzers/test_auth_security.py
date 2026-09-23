"""Tests for AuthSecurityAnalyzer."""
import pytest

from app.analyzers.auth_security import AuthSecurityAnalyzer
from tests.conftest import make_change


@pytest.fixture
def analyzer() -> AuthSecurityAnalyzer:
    return AuthSecurityAnalyzer()


@pytest.mark.parametrize("path", [
    "app/auth/login.py",
    "src/authentication/handler.py",
    "middleware/auth_middleware.py",
    "app/permissions/rbac.py",
    "src/security/crypto.py",
    "services/token_service.py",
    "app/session/manager.py",
    "routes/oauth.py",
    "auth.py",
    "security.py",
    "jwt.py",
    "app/identity/sso.py",
    "src/authorization/policy.py",
])
def test_detects_auth_files(analyzer: AuthSecurityAnalyzer, path: str) -> None:
    change = make_change([(path, 5, 2)])
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    assert signals[0].signal_type == "AUTH_SECURITY_CHANGE"
    assert signals[0].severity.value == "CRITICAL"
    assert signals[0].score_contribution == 35.0


def test_no_signal_for_regular_files(analyzer: AuthSecurityAnalyzer) -> None:
    change = make_change([
        ("src/models/user.py", 5, 0),
        ("src/api/products.py", 3, 1),
        ("README.md", 2, 1),
    ])
    assert analyzer.analyze(change) == []


def test_evidence_lists_auth_files(analyzer: AuthSecurityAnalyzer) -> None:
    change = make_change([
        ("app/auth/login.py", 5, 0),
        ("app/auth/logout.py", 3, 0),
        ("src/models/product.py", 10, 5),
    ])
    signals = analyzer.analyze(change)
    assert len(signals) == 1
    ev = signals[0].evidence
    assert "app/auth/login.py" in ev["auth_files"]
    assert "app/auth/logout.py" in ev["auth_files"]
    assert "src/models/product.py" not in ev["auth_files"]
