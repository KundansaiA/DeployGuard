"""Change Size Analyzer.

Detects unusually large changes based on files changed, additions, and deletions.

Thresholds (tunable via constructor):
  MEDIUM : files > 10  OR  total line changes > 300
  HIGH   : files > 25  OR  total line changes > 800
  CRITICAL: files > 50 OR  total line changes > 2000
"""
from app.analyzers.base import Analyzer, RiskSignal, SignalSeverity
from app.ingestion.types import ChangePayload

_NAME = "ChangeSizeAnalyzer"


class ChangeSizeAnalyzer:
    """Flags changes that are unusually large and therefore harder to review."""

    # (files_threshold, lines_threshold, severity, score, label)
    _THRESHOLDS = [
        (50, 2000, SignalSeverity.CRITICAL, 40.0, "critical"),
        (25, 800, SignalSeverity.HIGH, 25.0, "large"),
        (10, 300, SignalSeverity.MEDIUM, 15.0, "medium"),
    ]

    def analyze(self, change: ChangePayload) -> list[RiskSignal]:
        files = change.total_files
        lines = change.total_line_changes

        for file_thresh, line_thresh, severity, score, label in self._THRESHOLDS:
            if files > file_thresh or lines > line_thresh:
                return [
                    RiskSignal(
                        signal_type="LARGE_CHANGE",
                        severity=severity,
                        title=f"Change size is {label}",
                        description=(
                            f"This change modifies {files} file(s) with "
                            f"{change.total_additions} addition(s) and "
                            f"{change.total_deletions} deletion(s) "
                            f"({lines} total line changes). "
                            "Large changes are harder to review and carry higher deployment risk."
                        ),
                        score_contribution=score,
                        source_analyzer=_NAME,
                        evidence={
                            "files_changed": files,
                            "total_additions": change.total_additions,
                            "total_deletions": change.total_deletions,
                            "total_line_changes": lines,
                            "files_threshold": file_thresh,
                            "lines_threshold": line_thresh,
                        },
                    )
                ]
        return []


# Satisfy Analyzer protocol statically
_: Analyzer = ChangeSizeAnalyzer()
