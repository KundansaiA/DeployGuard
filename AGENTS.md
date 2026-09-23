# AGENTS.md

This file provides guidance to agents when working with code in this repository.

---

## Project: DeployGuard

A deployment-readiness platform. It ingests software changes, runs them through deterministic analyzers, produces a risk score and structured findings, and displays the results via a REST API and React dashboard. IBM Granite (via watsonx.ai) generates human-readable explanations of completed analyses — but the risk score is always deterministic.

---

## Architecture at a Glance

```
Change → Ingestion → Analyzers → RiskSignals → RiskEngine → AnalysisResult → API → Dashboard
                                                                ↑
                                                         IBM Granite (async, explanation only)
```

See [`docs/architecture.md`](docs/architecture.md) for the full diagram and design principles.

---

## Repository Layout

| Directory | Responsibility |
|---|---|
| `backend/` | FastAPI app, analyzers, risk engine, AI integration, DB models |
| `frontend/` | React + TypeScript dashboard |
| `infrastructure/` | Docker, Kubernetes, GitHub Actions CI |
| `tests/` | Integration and end-to-end tests (cross-layer) |
| `docs/` | Architecture and design docs |

---

## Backend Conventions (`backend/`)

**Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, pytest

### Key rules

- `app/models/` — SQLAlchemy ORM models only. Never import Pydantic schemas here.
- `app/schemas/` — Pydantic v2 request/response models only. Never import ORM models here.
- `app/api/v1/routes/` — FastAPI routers. Route handlers must be thin: validate input, call a service/engine function, return output. No business logic in routes.
- `app/analyzers/` — Each analyzer is a **stateless pure function**: `(Change) -> list[RiskSignal]`. No DB calls, no external I/O inside analyzers.
- `app/engine/` — Risk engine aggregates signals into a score (0–100) and severity tier (LOW / MEDIUM / HIGH / CRITICAL). Score algorithm must be deterministic for identical inputs.
- `app/ai/` — Granite integration. Called **after** the analysis result is persisted. If this call fails, the result is still returned with `explanation_text = None`.
- `app/config.py` — All settings via `pydantic-settings` (reads from environment / `.env`). Never hardcode config values.

### Import order (enforced by Ruff)
1. Standard library
2. Third-party (fastapi, sqlalchemy, pydantic, …)
3. Internal (`app.*`)

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Pydantic schemas: suffix with `Request` / `Response` / `Schema` (e.g. `AnalysisResultResponse`)
- ORM models: plain noun (e.g. `AnalysisResult`, `RiskSignal`)

### Error handling
- Raise `HTTPException` only in route handlers, not in services or engine code.
- Use Python built-in exceptions (`ValueError`, `RuntimeError`) in core logic; let routes translate them.

### Testing
- Unit tests live in `backend/tests/`, mirroring the `app/` structure.
- API tests use FastAPI `TestClient` (from `httpx`).
- Run all backend tests: `cd backend && pytest`
- Run a single test file: `cd backend && pytest tests/path/to/test_file.py`
- Run a single test: `cd backend && pytest tests/path/to/test_file.py::test_function_name`
- Tests must be run from the `backend/` directory (not project root) — Alembic and `.env` paths are relative.

---

## Frontend Conventions (`frontend/`)

**Stack:** React 18, TypeScript 5, Vite

- All components in `src/components/`, pages in `src/pages/`.
- API calls go through `src/api/` — never call `fetch`/`axios` directly from components.
- Types shared across the app live in `src/types/`.
- Use TypeScript strict mode (`"strict": true` in `tsconfig.json`). No `any` unless absolutely justified with a comment.
- Component files: `PascalCase.tsx`; utility/hook files: `camelCase.ts`.
- Run tests: `cd frontend && npm test`
- Run a single test: `cd frontend && npm test -- path/to/file.test.tsx`

---

## Database / Migrations

- All schema changes must go through Alembic. Never `ALTER TABLE` outside a migration.
- Generate a migration: `cd backend && alembic revision --autogenerate -m "description"`
- Apply migrations: `cd backend && alembic upgrade head`
- Migrations are forward-only by design — no rollback support planned.

---

## Infrastructure

- `infrastructure/docker/docker-compose.yml` — runs the full stack locally (backend + frontend + postgres).
- `infrastructure/kubernetes/` — production deployment manifests.
- `infrastructure/ci/` — GitHub Actions workflow files.

---

## AI Integration Notes

- IBM Granite model: `ibm/granite-3-3-8b-instruct` (configurable via `WATSONX_MODEL_ID`)
- SDK: `ibm-watsonx-ai` (Python) — install separately: `pip install ibm-watsonx-ai`
- Granite is called **on-demand** via `POST /api/v1/analyses/{id}/explanation`. The deterministic analysis always succeeds first.
- Required env vars to enable: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`. Leave empty to disable gracefully.
- Optional: `WATSONX_URL` (default: us-south), `WATSONX_MODEL_ID`, `WATSONX_TIMEOUT_SECS`
- Provider abstraction: `app/ai/base.py` defines `ExplanationProvider` protocol — swap out `WatsonxGraniteProvider` for any other provider without touching application code.
- `explanation_status` field on `Analysis`: `"none"` | `"pending"` | `"done"` | `"failed"`.
- Tests: mock the provider via `unittest.mock.patch` — no real credentials needed.

---

## Environment Setup

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # set DB_URL, WATSONX_* vars

# Frontend
cd frontend
npm install
```
