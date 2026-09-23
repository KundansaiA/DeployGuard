"""Analysis API routes.

Endpoints:
  POST   /api/v1/analyses                        — submit a change for analysis
  GET    /api/v1/analyses                        — list analyses (paginated)
  GET    /api/v1/analyses/{id}                   — retrieve a single analysis
  POST   /api/v1/analyses/{id}/explanation       — generate (or return cached) AI explanation
  GET    /api/v1/analyses/{id}/explanation       — retrieve explanation status + text
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.base import ExplanationProvider  # used in _explanation_provider type annotation
from app.ai.service import generate_explanation
from app.database import get_db
from app.ingestion.pipeline import run_analysis
from app.models.analysis import Analysis
from app.schemas.analysis import (
    AnalysisListResponse,
    AnalysisResponse,
    ExplanationResponse,
    SubmitChangeRequest,
)

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisResponse, status_code=201)
def create_analysis(
    request: SubmitChangeRequest,
    db: Session = Depends(get_db),
) -> Analysis:
    """Submit a software change for deployment-risk analysis.

    Runs the full deterministic analyzer pipeline and persists the result.
    The AI explanation is not generated automatically — call
    POST /analyses/{id}/explanation to request one.
    """
    return run_analysis(request, db)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> Analysis:
    """Retrieve a single analysis by ID."""
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found")
    return analysis


@router.get("", response_model=AnalysisListResponse)
def list_analyses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> AnalysisListResponse:
    """List analyses ordered by most recent first."""
    from sqlalchemy import select, func

    total: int = db.scalar(select(func.count()).select_from(Analysis)) or 0
    rows = db.scalars(
        select(Analysis).order_by(Analysis.created_at.desc()).offset(skip).limit(limit)
    ).all()

    return AnalysisListResponse(items=list(rows), total=total)


# Module-level provider override — replace in tests via `app.api.v1.routes.analyses._explanation_provider`
_explanation_provider: ExplanationProvider | None = None


@router.post("/{analysis_id}/explanation", response_model=ExplanationResponse)
def request_explanation(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> ExplanationResponse:
    """Generate (or return cached) an AI explanation for an analysis.

    - If explanation_status is "done", returns the cached explanation immediately.
    - Otherwise calls the configured AI provider synchronously and persists the result.
    - The deterministic analysis result is never affected by provider failures.
    """
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found")

    if analysis.explanation_status != "done":
        analysis = generate_explanation(analysis, db, provider=_explanation_provider)

    return ExplanationResponse(
        status=analysis.explanation_status,  # type: ignore[arg-type]
        text=analysis.explanation_text,
    )


@router.get("/{analysis_id}/explanation", response_model=ExplanationResponse)
def get_explanation(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> ExplanationResponse:
    """Retrieve the current explanation status and text for an analysis.

    Does NOT trigger generation — use POST to request generation.
    """
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found")

    return ExplanationResponse(
        status=analysis.explanation_status,  # type: ignore[arg-type]
        text=analysis.explanation_text,
    )
