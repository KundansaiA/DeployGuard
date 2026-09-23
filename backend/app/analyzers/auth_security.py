"""Authentication / Security Analyzer.

Detects changes that touch authentication, authorization, permissions,
security-sensitive middleware, tokens, sessions, or identity systems.

These changes carry elevated risk because bugs in auth code can expose
the entire system to unauthorized access or privilege escalation.
"""
import re

from app.analyzers.base import Analyzer, RiskSignal, SignalSeverity
from app.ingestion.types import ChangePayload

_NAME = "AuthSecurityAnalyzer"

_AUTH_PATH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(^|[/_-])(auth|authn|authz|authentication|authorization)[/_.-]", re.IGNORECASE),
    re.compile(r"(^|[/_-])(permission|permissions|role|roles|rbac|acl|access)[/_.-]", re.IGNORECASE),
    re.compile(r"(^|[/_-])(security|secure|identity|sso|oauth|oidc|saml)[/_.-]", re.IGNORECASE),
    re.compile(r"(^|[/_-])(token|session|cookie|jwt|credential|password|secret)[/_.-]", re.IGNORECASE),
    re.compile(r"(^|[/_-])(login|logout|signup|register|forgot.?password)[/_.-]", re.IGNORECASE),
    re.compile(r"middleware[/_.-]?(auth|security|permission)", re.IGNORECASE),
]

_AUTH_FILENAME_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"auth\.(py|ts|js|go|java|rb|cs)$", re.IGNORECASE),
    re.compile(r"security\.(py|ts|js|go|java|rb|cs)$", re.IGNORECASE),
    re.compile(r"permissions?\.(py|ts|js|go|java|rb|cs)$", re.IGNORECASE),
    re.compile(r"jwt\.(py|ts|js|go|java|rb|cs)$", re.IGNORECASE),
]


def _is_auth_file(path: str) -> bool:
    return any(p.search(path) for p in _AUTH_PATH_PATTERNS) or any(
        p.search(path) for p in _AUTH_FILENAME_PATTERNS
    )


class AuthSecurityAnalyzer:
    """Flags changes touching authentication, authorization, or security-sensitive code."""

    def analyze(self, change: ChangePayload) -> list[RiskSignal]:
        auth_files = [f for f in change.changed_files if _is_auth_file(f.path)]
        if not auth_files:
            return []

        paths = [f.path for f in auth_files]
        return [
            RiskSignal(
                signal_type="AUTH_SECURITY_CHANGE",
                severity=SignalSeverity.CRITICAL,
                title=f"Authentication/security code modified ({len(auth_files)} file(s))",
                description=(
                    "This change modifies authentication, authorization, or security-sensitive code. "
                    "Errors in this area can expose the system to unauthorized access or "
                    "privilege escalation. Requires mandatory security review before deployment."
                ),
                score_contribution=35.0,
                source_analyzer=_NAME,
                evidence={"auth_files": paths},
            )
        ]


_: Analyzer = AuthSecurityAnalyzer()
