# Backend — DeployGuard

FastAPI application containing:

- `app/main.py` — FastAPI app factory and startup
- `app/config.py` — Settings loaded from environment via pydantic-settings
- `app/database.py` — SQLAlchemy engine and session factory
- `app/api/v1/routes/` — FastAPI routers (one file per resource)
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic v2 request/response schemas
- `app/ingestion/` — Change ingestion and normalization
- `app/analyzers/` — Stateless risk analyzers
- `app/engine/` — Deterministic risk scoring engine
- `app/ai/` — IBM watsonx.ai / Granite integration
- `alembic/` — Database migrations
- `tests/` — pytest unit and API tests

---

## Local Development

### 1 — Start PostgreSQL

From the repository root:

```bash
docker compose -f infrastructure/docker/docker-compose.yml up postgres -d
```

PostgreSQL will be available at `localhost:5432` with:
- user: `deployguard`
- password: `deployguard`
- database: `deployguard`

### 2 — Set up the Python environment

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 3 — Configure environment variables

```bash
cp .env.example .env
# Edit .env if you want to override DB_URL or add watsonx.ai credentials.
# The defaults work with the Docker Compose postgres container.
```

The default `DB_URL` in `.env.example` is:
```
DB_URL=postgresql://deployguard:deployguard@localhost:5432/deployguard
```

### 4 — Run database migrations

```bash
# Must be run from the backend/ directory
alembic upgrade head
```

This creates the `analyses` and `risk_signals` tables, the cascading foreign
key from `risk_signals → analyses`, and all indexes.

To check current migration state:
```bash
alembic current
```

To generate a new migration after changing models:
```bash
alembic revision --autogenerate -m "describe your change"
# Review the generated file in alembic/versions/ before applying
alembic upgrade head
```

### 5 — Start the FastAPI server

```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

---

## Frontend

From the repository root (in a separate terminal):

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at `http://localhost:5173`.

---

## Testing

All tests use an in-memory SQLite database — no running PostgreSQL required.

```bash
# All tests
pytest

# Single file
pytest tests/analyzers/test_change_size.py

# Single test
pytest tests/analyzers/test_change_size.py::test_critical_signal_on_file_threshold
```

---

## Database Migrations Reference

| Command | Effect |
|---|---|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic current` | Show current revision |
| `alembic history` | Show migration history |
| `alembic downgrade -1` | Roll back one migration |
| `alembic revision --autogenerate -m "..."` | Generate migration from model diff |
| `alembic upgrade head --sql` | Preview the SQL without applying it |

> **Important:** Migrations are forward-only by convention. Avoid relying on
> `downgrade` in production — use additive schema changes where possible.

---

## Environment Variables

| Variable | Default | Required |
|---|---|---|
| `DB_URL` | `postgresql://deployguard:deployguard@localhost:5432/deployguard` | Yes |
| `SECRET_KEY` | `change-me` | Yes (production) |
| `LOG_LEVEL` | `INFO` | No |
| `WATSONX_API_KEY` | _(empty)_ | Only for AI explanations |
| `WATSONX_PROJECT_ID` | _(empty)_ | Only for AI explanations |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | No |
| `WATSONX_MODEL_ID` | `ibm/granite-3-3-8b-instruct` | No |
| `WATSONX_TIMEOUT_SECS` | `30` | No |

Leave `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` empty to disable AI
explanations. All deterministic analysis will still work normally.
