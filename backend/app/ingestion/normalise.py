"""Ingestion layer: converts API request payloads into internal ChangePayload objects."""
from app.ingestion.types import ChangePayload, ChangedFile
from app.schemas.analysis import SubmitChangeRequest


def normalise_change(request: SubmitChangeRequest) -> ChangePayload:
    """Convert a SubmitChangeRequest into an immutable ChangePayload.

    This is the only place where API schemas touch internal ingestion types.
    """
    files = tuple(
        ChangedFile(
            path=f.path,
            additions=f.additions,
            deletions=f.deletions,
            patch=f.patch,
        )
        for f in request.changed_files
    )
    return ChangePayload(
        repository=request.repository,
        branch=request.branch,
        commit_sha=request.commit_sha,
        changed_files=files,
    )
