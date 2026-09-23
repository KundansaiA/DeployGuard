"""DeployGuard FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes.analyses import router as analyses_router
from app.config import settings

app = FastAPI(
    title="DeployGuard",
    description="Deployment-readiness analysis API",
    version="0.1.0",
)

# CORS — origins are controlled by the CORS_ORIGINS environment variable.
# Local dev default: http://localhost:5173 (Vite dev server).
# Production: set CORS_ORIGINS to your deployed frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(analyses_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
