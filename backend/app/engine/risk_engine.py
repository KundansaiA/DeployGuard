"""Deterministic Risk Engine.

Aggregates RiskSignals into a bounded 0–100 score and assigns a severity tier.

Scoring rules
─────────────
1. Sum all signal score_contribution values.
2. Cap the result at 100 (no analysis can exceed 100).
3. Map the capped score to a SeverityTier:

   Score range  │ Tier
   ─────────────┼──────────
     0 –  24    │ LOW
    25 –  49    │ MEDIUM
    50 –  74    │ HIGH
    75 – 100    │ CRITICAL

The mapping is defined in SEVERITY_THRESHOLDS and is the single source
of truth for severity determination throughout the application.
"""
from dataclasses import dataclass

from app.analyzers.base import RiskSignal
from app.models.analysis import SeverityTier

# (minimum_score_inclusive, tier)
# Evaluated highest-first; first match wins.
SEVERITY_THRESHOLDS: list[tuple[float, SeverityTier]] = [
    (75.0, SeverityTier.CRITICAL),
    (50.0, SeverityTier.HIGH),
    (25.0, SeverityTier.MEDIUM),
    (0.0, SeverityTier.LOW),
]

MAX_SCORE: float = 100.0


@dataclass(frozen=True)
class EngineResult:
    """Output of the risk engine for a set of signals."""

    score: float
    severity: SeverityTier
    signals: list[RiskSignal]


def calculate_severity(score: float) -> SeverityTier:
    """Map a numeric score to a SeverityTier using SEVERITY_THRESHOLDS.

    Args:
        score: A value in [0, 100].

    Returns:
        The matching SeverityTier.
    """
    for threshold, tier in SEVERITY_THRESHOLDS:
        if score >= threshold:
            return tier
    return SeverityTier.LOW


def run_engine(signals: list[RiskSignal]) -> EngineResult:
    """Aggregate signals into a risk score and severity tier.

    Args:
        signals: All RiskSignal objects produced by the analyzer pipeline.

    Returns:
        EngineResult with the capped score, severity tier, and original signals.
    """
    raw_score = sum(s.score_contribution for s in signals)
    score = min(raw_score, MAX_SCORE)
    severity = calculate_severity(score)
    return EngineResult(score=score, severity=severity, signals=signals)
