"""Ingestion domain: internal representations of a submitted change.

These are pure Python dataclasses — not ORM models, not Pydantic schemas.
They are created by the ingestion layer and passed to analyzers.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChangedFile:
    """Immutable representation of a single changed file."""

    path: str
    additions: int = 0
    deletions: int = 0
    patch: str | None = None

    @property
    def total_changes(self) -> int:
        return self.additions + self.deletions

    @property
    def filename(self) -> str:
        """Basename of the file path."""
        return self.path.rsplit("/", 1)[-1]

    @property
    def extension(self) -> str:
        """File extension including the dot, lower-cased. Empty string if none."""
        if "." in self.filename:
            return "." + self.filename.rsplit(".", 1)[-1].lower()
        return ""


@dataclass(frozen=True)
class ChangePayload:
    """Normalised internal representation of a submitted software change."""

    repository: str
    branch: str
    commit_sha: str
    changed_files: tuple[ChangedFile, ...] = field(default_factory=tuple)

    @property
    def total_files(self) -> int:
        return len(self.changed_files)

    @property
    def total_additions(self) -> int:
        return sum(f.additions for f in self.changed_files)

    @property
    def total_deletions(self) -> int:
        return sum(f.deletions for f in self.changed_files)

    @property
    def total_line_changes(self) -> int:
        return self.total_additions + self.total_deletions
