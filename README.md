# DeployGuard

DeployGuard is a deployment-readiness platform that analyzes software changes before they are deployed, detects potential risk signals, calculates a deterministic risk score, and surfaces the results through a REST API and React dashboard.

## What it does

Before a deployment ships, DeployGuard ingests the diff or change set, runs it through a pipeline of deterministic analyzers (coverage drop, dependency change, secrets exposure, breaking schema changes, etc.), normalizes the findings into risk signals, and produces a risk score and structured result. IBM Granite then generates a human-readable explanation of the findings. The goal: give the team a clear, auditable signal before they push to production.

## Technology Stack

| Layer | Technology |
|---|---|
| Backend API | Python · FastAPI · SQLAlchemy |
| Database | PostgreSQL · Alembic (migrations) |
| Frontend | React · TypeScript |
| AI / Explanations | IBM watsonx.ai · IBM Granite |
| Containers | Docker · Docker Compose |
| Orchestration | Kubernetes |
| CI/CD | GitHub Actions |

## Architecture Overview

```
Software change
  → change ingestion
  → deterministic analyzers
  → normalized risk signals
  → deterministic risk engine
  → analysis result
  → REST API
  → React dashboard
```

IBM Granite provides human-readable explanations of completed analyses. The core risk detection and scoring is deterministic — AI explains results, it does not drive them.

## Repository Structure

```
deployguard/
├── backend/            # FastAPI application, analyzers, risk engine
├── frontend/           # React + TypeScript dashboard
├── infrastructure/     # Docker, Kubernetes, CI/CD configs
├── tests/              # Integration and end-to-end tests
├── docs/               # Architecture and design documentation
└── AGENTS.md           # AI agent guidance for this codebase
```

## Getting Started

> Prerequisites: Python 3.11+, Node.js 18+, Docker, PostgreSQL

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in DB_URL, WATSONX_API_KEY, etc.
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Full stack (Docker Compose)

```bash
docker compose up --build
```

## Development

- API docs available at `http://localhost:8000/docs` when the backend is running.
- Frontend dev server runs on `http://localhost:5173` by default.
- See [`docs/architecture.md`](docs/architecture.md) for the full system design.
- See [`AGENTS.md`](AGENTS.md) for coding conventions and project-specific rules.

## License

MIT
