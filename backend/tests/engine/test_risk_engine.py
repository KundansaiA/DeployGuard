"""Tests for the deterministic RiskEngine."""
import pytest

from app.analyzers.base import RiskSignal, SignalSeverity
from app.engine.risk_engine import (
    MAX_SCORE,
    SEVERITY_THRESHOLDS,
    calculate_severity,
    run_engine,
)
from app.models.analysis import SeverityTier


def make_signal(score: float, severity: SignalSeverity = SignalSeverity.LOW) -> RiskSignal:
    return RiskSignal(
        signal_type="TEST_SIGNAL",
        severity=severity,
        title="Test",
        description="Test signal",
        score_contribution=score,
        source_analyzer="test",
    )


# ─────────────────────────────────────────────────────────────
# calculate_severity
# ─────────────────────────────────────────────────────────────

class TestCalculateSeverity:
    def test_score_0_is_low(self) -> None:
        assert calculate_severity(0.0) == SeverityTier.LOW

    def test_score_24_is_low(self) -> None:
        assert calculate_severity(24.9) == SeverityTier.LOW

    def test_score_25_is_medium(self) -> None:
        assert calculate_severity(25.0) == SeverityTier.MEDIUM

    def test_score_49_is_medium(self) -> None:
        assert calculate_severity(49.9) == SeverityTier.MEDIUM

    def test_score_50_is_high(self) -> None:
        assert calculate_severity(50.0) == SeverityTier.HIGH

    def test_score_74_is_high(self) -> None:
        assert calculate_severity(74.9) == SeverityTier.HIGH

    def test_score_75_is_critical(self) -> None:
        assert calculate_severity(75.0) == SeverityTier.CRITICAL

    def test_score_100_is_critical(self) -> None:
        assert calculate_severity(100.0) == SeverityTier.CRITICAL

    def test_boundary_thresholds_match_constants(self) -> None:
        """SEVERITY_THRESHOLDS must be consistent with actual behaviour."""
        for threshold, expected_tier in SEVERITY_THRESHOLDS:
            assert calculate_severity(threshold) == expected_tier


# ─────────────────────────────────────────────────────────────
# run_engine — score calculation
# ─────────────────────────────────────────────────────────────

class TestRunEngine:
    def test_no_signals_gives_zero_score(self) -> None:
        result = run_engine([])
        assert result.score == 0.0
        assert result.severity == SeverityTier.LOW

    def test_single_signal_score(self) -> None:
        result = run_engine([make_signal(30.0)])
        assert result.score == 30.0
        assert result.severity == SeverityTier.MEDIUM

    def test_multiple_signals_summed(self) -> None:
        signals = [make_signal(20.0), make_signal(15.0), make_signal(10.0)]
        result = run_engine(signals)
        assert result.score == 45.0
        assert result.severity == SeverityTier.MEDIUM

    def test_score_capped_at_100(self) -> None:
        # Total would be 200 without capping
        signals = [make_signal(50.0)] * 4
        result = run_engine(signals)
        assert result.score == MAX_SCORE
        assert result.score <= 100.0

    def test_score_exactly_100_not_exceeded(self) -> None:
        signals = [make_signal(100.0)]
        result = run_engine(signals)
        assert result.score == 100.0

    def test_score_slightly_over_100_capped(self) -> None:
        signals = [make_signal(60.0), make_signal(50.0)]
        result = run_engine(signals)
        assert result.score == 100.0

    def test_signals_preserved_in_result(self) -> None:
        signals = [make_signal(20.0), make_signal(30.0)]
        result = run_engine(signals)
        assert len(result.signals) == 2

    def test_severity_at_capped_score_is_critical(self) -> None:
        signals = [make_signal(100.0)]
        result = run_engine(signals)
        assert result.severity == SeverityTier.CRITICAL

    def test_high_severity_threshold(self) -> None:
        result = run_engine([make_signal(50.0)])
        assert result.severity == SeverityTier.HIGH

    def test_medium_severity_threshold(self) -> None:
        result = run_engine([make_signal(25.0)])
        assert result.severity == SeverityTier.MEDIUM

    def test_score_precision_summed_correctly(self) -> None:
        signals = [make_signal(15.0), make_signal(8.0)]
        result = run_engine(signals)
        assert abs(result.score - 23.0) < 1e-9

    def test_negative_contribution_rejected(self) -> None:
        with pytest.raises(ValueError, match="score_contribution must be >= 0"):
            make_signal(-1.0)
