# AGENTS.md — Agent Mode

This file provides guidance to agents when working with code in this repository.

## Coding Rules (Non-Obvious)

- **Analyzer contract is strict**: every analyzer in `backend/app/analyzers/` must be a pure function with signature `(change: Change) -> list[RiskSignal]`. Adding DB calls, HTTP calls, or side effects to an analyzer will break the pipeline contract.
- **ORM ↔ Schema separation is hard**: `app/models/` and `app/schemas/` must never import each other. Conversion happens only in route handlers or service layer via explicit mapping.
- **Risk engine is the single source of truth for scoring**: never compute or modify the risk score anywhere except `backend/app/engine/`. Dashboard or API must not re-derive scores.
- **Granite is fire-and-forget**: the `app/ai/` module must not block the API response. Explanation generation is async and its failure must not raise an exception that propagates to the caller.
- **Alembic autogenerate will miss enums**: SQLAlchemy Enum columns need manual review after `alembic revision --autogenerate` — Alembic does not always detect enum changes correctly in PostgreSQL.
- **Tests must run from `backend/`**: pytest is configured relative to that directory. Running from project root will fail to find `conftest.py` and `.env.example`.
- **Frontend API calls only through `src/api/`**: components must not call fetch/axios directly. All API interaction goes through the typed client modules in `frontend/src/api/`.
- **`pydantic-settings` reads `.env` automatically**: do not load dotenv manually in application code — `config.py` handles it. Adding a second dotenv load will cause double-parsing issues.
