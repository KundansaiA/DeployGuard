# DeployGuard — Architecture

## Purpose

DeployGuard intercepts software changes before they reach production and produces an auditable, deterministic deployment-readiness score. IBM Granite (via watsonx.ai) adds a human-readable explanation **after** the deterministic result is persisted — it does not alter the score or signals.

---

## High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  Client  (GitHub webhook / API call / CI step)                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │  POST /api/v1/analyses
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FastAPI — Change Ingestion Layer  (app/ingestion/)                 │
│  • Validates & normalises the incoming SubmitChangeRequest          │
│  • Builds an immutable ChangePayload dataclass                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Deterministic Analyzer Pipeline  (app/analyzers/)                  │
│  Each analyzer: (ChangePayload) → list[RiskSignal]                  │
│                                                                     │
│  ┌───────────────────┐  ┌──────────────────────┐                   │
│  │ ChangeSizeAnalyzer│  │ DatabaseMigration     │                   │
│  └───────────────────┘  │ Analyzer             │                   │
│  ┌───────────────────┐  └──────────────────────┘                   │
│  │ AuthSecurity      │  ┌──────────────────────┐                   │
│  │ Analyzer          │  │ Infrastructure       │                   │
│  └───────────────────┘  │ Analyzer             │                   │
│  ┌───────────────────┐  └──────────────────────┘                   │
│  │ TestCoverage      │  ┌──────────────────────┐                   │
│  │ Analyzer          │  │ Dependency Analyzer  │                   │
│  └───────────────────┘  └──────────────────────┘                   │
│  ┌───────────────────┐                                              │
│  │ CriticalFile      │  (add new analyzers in app/analyzers/        │
│  │ Analyzer          │   and register in __init__.py)               │
│  └───────────────────┘                                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │ list[RiskSignal]
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Deterministic Risk Engine  (app/engine/)                           │
│  • Sums signal.score_contribution values                            │
│  • Caps score at 100                                                │
│  • Maps score → SeverityTier (LOW / MEDIUM / HIGH / CRITICAL)       │
│                                                                     │
│  Score thresholds:                                                  │
│    0 – 24  → LOW                                                    │
│   25 – 49  → MEDIUM                                                 │
│   50 – 74  → HIGH                                                   │
│   75 – 100 → CRITICAL                                               │
└────────────────────────────┬────────────────────────────────────────┘
                             │ EngineResult(score, severity, signals)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Persistence  (app/ingestion/pipeline.py)                           │
│  • Writes Analysis + RiskSignalRecord rows to PostgreSQL            │
│  • explanation_status = "none" at this point                        │
│  • Returns persisted Analysis ORM object                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │  Analysis returned to caller
                    ─────────┴──────────────────────
                    │                              │
                    ▼                              ▼
       POST /api/v1/analyses           POST /analyses/{id}/explanation
       returns immediately             (separate, on-demand call)
                                                   │
                                                   ▼
                             ┌─────────────────────────────────────────┐
                             │  AI Explanation Layer  (app/ai/)         │
                             │                                          │
                             │  ExplanationProvider protocol            │
                             │  ↳ WatsonxGraniteProvider (default)     │
                             │                                          │
                             │  • Builds AnalysisContext from Analysis  │
                             │  • Sends structured prompt to Granite    │
                             │  • Stores explanation_text in Analysis   │
                             │  • Sets explanation_status = "done"      │
                             │    (or "failed" on any error)            │
                             │                                          │
                             │  CRITICAL: AI never touches risk_score,  │
                             │  severity, or signals.                   │
                             └─────────────────────────────────────────┘
                                                   │
                    ───────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  REST API  (app/api/v1/routes/)                                     │
│                                                                     │
│  POST   /api/v1/analyses                  — submit change           │
│  GET    /api/v1/analyses                  — list (paginated)        │
│  GET    /api/v1/analyses/{id}             — get analysis            │
│  POST   /api/v1/analyses/{id}/explanation — generate explanation    │
│  GET    /api/v1/analyses/{id}/explanation — get explanation status  │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  React Dashboard  (frontend/src/)                                   │
│                                                                     │
│  /analyses           — AnalysisListPage                             │
│  /analyses/:id       — AnalysisDetailPage                           │
│    • Risk score + severity badge                                    │
│    • Signal breakdown with evidence                                 │
│    • AiExplanation component (4 states: none/loading/done/failed)  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Domain Concepts

| Concept | Description |
|---|---|
| **ChangePayload** | Immutable internal representation of a submitted change |
| **ChangedFile** | Single file in a change: path, additions, deletions, optional patch |
| **RiskSignal** | One finding from an analyzer: type, severity, score contribution, evidence |
| **EngineResult** | Aggregated result: capped score (0–100), severity tier, signal list |
| **Analysis** | Persisted record: all of the above plus explanation status/text |
| **ExplanationProvider** | Protocol: `explain(AnalysisContext) → ExplanationResult` |
| **AnalysisContext** | Immutable snapshot of an Analysis passed to the AI provider |

---

## Analyzer Score Contributions (defaults)

| Analyzer | Signal Type | Score |
|---|---|---|
| ChangeSizeAnalyzer | LARGE_CHANGE | 15 / 25 / 40 (medium/high/critical) |
| DatabaseMigrationAnalyzer | DATABASE_MIGRATION | 30 |
| AuthSecurityAnalyzer | AUTH_SECURITY_CHANGE | 35 |
| InfrastructureAnalyzer | INFRASTRUCTURE_CHANGE | 25 |
| TestCoverageAnalyzer | NO_TEST_CHANGES | 20 |
| TestCoverageAnalyzer | LOW_TEST_COVERAGE_RATIO | 10 |
| DependencyAnalyzer | LOCKFILE_CHANGED | 15 |
| DependencyAnalyzer | DEPENDENCY_MANIFEST_CHANGED | 8 |
| CriticalFileAnalyzer | CRITICAL_FILE_MODIFIED | 10–35 (by file type) |

Scores accumulate and are capped at 100.

---

## AI Integration (IBM Granite)

```
AnalysisContext ──→ WatsonxGraniteProvider ──→ ibm-watsonx-ai SDK
                                                       │
                              ┌───────────────────────┘
                              ▼
                  ibm/granite-3-3-8b-instruct
                  (chat endpoint, max_new_tokens=800)
                              │
                              ▼
                  ExplanationResult(status, text)
                              │
              ┌───────────────┴──────────────┐
              ▼                              ▼
         status="done"               status="failed"
         text=<explanation>          text=None
         (persisted)                 (analysis still returned)
```

### Graceful failure contract
Every error path in `WatsonxGraniteProvider.explain()` returns `ExplanationResult(status="failed")` — it never raises. The calling service persists the failed status and returns the unchanged deterministic result. The API always returns 200 for the explanation endpoint, with `status` indicating the outcome.

### Configuration
| Variable | Required | Default |
|---|---|---|
| `WATSONX_API_KEY` | Yes (for AI) | `""` |
| `WATSONX_PROJECT_ID` | Yes (for AI) | `""` |
| `WATSONX_URL` | No | `https://us-south.ml.cloud.ibm.com` |
| `WATSONX_MODEL_ID` | No | `ibm/granite-3-3-8b-instruct` |
| `WATSONX_TIMEOUT_SECS` | No | `30` |

AI is disabled (gracefully) when `WATSONX_API_KEY` or `WATSONX_PROJECT_ID` is empty.

---

## Backend Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # pydantic-settings (reads .env)
│   ├── database.py          # SQLAlchemy engine + session factory
│   │
│   ├── api/v1/routes/
│   │   └── analyses.py      # All analysis + explanation endpoints
│   │
│   ├── models/
│   │   └── analysis.py      # Analysis + RiskSignalRecord ORM models
│   │
│   ├── schemas/
│   │   └── analysis.py      # Pydantic request/response schemas
│   │
│   ├── ingestion/
│   │   ├── types.py         # ChangePayload, ChangedFile dataclasses
│   │   ├── normalise.py     # SubmitChangeRequest → ChangePayload
│   │   └── pipeline.py      # Full analysis pipeline orchestrator
│   │
│   ├── analyzers/
│   │   ├── base.py          # RiskSignal, Analyzer protocol
│   │   ├── change_size.py
│   │   ├── database_migration.py
│   │   ├── auth_security.py
│   │   ├── infrastructure.py
│   │   ├── test_coverage.py
│   │   ├── dependency.py
│   │   ├── critical_files.py
│   │   └── __init__.py      # build_analyzer_registry()
│   │
│   ├── engine/
│   │   └── risk_engine.py   # run_engine(), calculate_severity()
│   │
│   └── ai/
│       ├── base.py          # ExplanationProvider protocol + types
│       ├── watsonx.py       # WatsonxGraniteProvider
│       └── service.py       # generate_explanation() — orchestrates AI call
│
├── tests/
│   ├── analyzers/           # Unit tests for each analyzer
│   ├── engine/              # Risk engine + severity boundary tests
│   ├── api/                 # API integration tests (TestClient + SQLite)
│   └── ai/                  # AI provider, service, and API endpoint tests
│
├── alembic/                 # Database migrations
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml           # pytest + ruff + mypy config
└── .env.example
```

---

## Design Principles

1. **Determinism first** — same input always produces same score and signals. AI never touches scoring.
2. **Analyzer isolation** — pure function `(ChangePayload) → list[RiskSignal]`. No DB, no I/O, no state.
3. **Thin API routes** — routes validate input, call service/engine, return output. Zero business logic.
4. **Schema / ORM separation** — `app/models/` and `app/schemas/` never import each other.
5. **Migration-safe DB** — all schema changes via Alembic. Forward-only.
6. **AI is optional** — empty `WATSONX_API_KEY` → AI disabled gracefully, zero impact on analysis.
7. **Provider abstraction** — `ExplanationProvider` protocol means any AI provider can replace Granite.

---

## Testing Strategy

| Layer | Tool | Location | Count |
|---|---|---|---|
| Analyzer units | pytest | `backend/tests/analyzers/` | 7 files |
| Risk engine units | pytest | `backend/tests/engine/` | 1 file |
| API integration | pytest + TestClient + SQLite | `backend/tests/api/` | 1 file |
| AI base types | pytest | `backend/tests/ai/test_base.py` | 1 file |
| AI provider (mocked) | pytest + unittest.mock | `backend/tests/ai/test_watsonx_provider.py` | 1 file |
| AI service (mocked) | pytest + unittest.mock | `backend/tests/ai/test_service.py` | 1 file |
| Explanation API | pytest + TestClient | `backend/tests/ai/test_explanation_api.py` | 1 file |
| Frontend component | Vitest + RTL | `frontend/src/__tests__/` | 1 file |

**No real IBM credentials required to run any tests.**

---

## Infrastructure

```
infrastructure/
├── docker/
│   └── docker-compose.yml       # postgres + backend + frontend
├── kubernetes/
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   └── postgres-statefulset.yaml
└── ci/
    └── github-actions/ci.yml    # lint + test + build on push/PR
```
