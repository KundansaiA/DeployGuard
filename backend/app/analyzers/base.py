"""Analyzer interface and shared RiskSignal dataclass.

Every analyzer must follow the Analyzer protocol:
    def analyze(change: ChangePayload) -> list[RiskSignal]

Analyzers are stateless pure functions — no DB, no I/O, no side effects.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from app.ingestion.types import ChangePayload


class SignalSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskSignal:
    """A single risk finding produced by an analyzer."""

    signal_type: str
    severity: SignalSeverity
    title: str
    description: str
    score_contribution: float
    source_analyzer: str
    evidence: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.score_contribution < 0:
            raise ValueError("score_contribution must be >= 0")


class Analyzer(Protocol):
    """Protocol that every analyzer must satisfy."""

    def analyze(self, change: ChangePayload) -> list[RiskSignal]:
        ...
