"""Shared pytest fixtures and test helpers."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app as fastapi_app
import app.models.analysis  # noqa: F401 — ensure ORM models are registered with Base.metadata
from app.ingestion.types import ChangePayload, ChangedFile

# ─────────────────────────────────────────────────────────────
# In-memory SQLite DB for tests
#
# StaticPool is required so every connection the engine opens
# shares the SAME in-memory SQLite database.  Without it, each
# new connection gets an empty database and "no such table" errors.
# ─────────────────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///:memory:"

_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(scope="function")
def db() -> Session:  # type: ignore[override]
    """Provide a clean DB session backed by an in-memory SQLite database."""
    Base.metadata.create_all(bind=_engine)
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> TestClient:
    """Provide a FastAPI TestClient that uses the in-memory test DB."""
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────
# Convenience factories
# ─────────────────────────────────────────────────────────────

def make_change(
    files: list[tuple[str, int, int]] | None = None,
    repository: str = "org/repo",
    branch: str = "main",
    commit_sha: str = "abc1234",
) -> ChangePayload:
    """Build a ChangePayload from a list of (path, additions, deletions) tuples."""
    changed_files = tuple(
        ChangedFile(path=path, additions=adds, deletions=dels)
        for path, adds, dels in (files or [])
    )
    return ChangePayload(
        repository=repository,
        branch=branch,
        commit_sha=commit_sha,
        changed_files=changed_files,
    )
