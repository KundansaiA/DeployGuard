# AGENTS.md — Plan Mode

This file provides guidance to agents when working with code in this repository.

## Architectural Constraints (Non-Obvious)

- **Analyzers must stay stateless and pure**: the pipeline design assumes analyzers can be run in any order, in parallel, and retried safely. Any stateful analyzer breaks this.
- **Score algorithm must be deterministic**: the same set of RiskSignals must always produce the same score. Randomness, timestamps, or external lookups must not influence scoring.
- **Granite is explanation-only by design**: adding AI to the scoring path would break auditability. This is a deliberate architectural constraint, not a limitation to work around.
- **Forward-only migrations**: Alembic migrations are append-only. Plan schema changes to be additive where possible (new nullable columns, new tables). Breaking changes require careful staged rollout.
- **Single PostgreSQL instance assumed**: the current design does not account for read replicas or sharding. Keep queries simple and index-friendly.
- **API versioning is `v1` from day one**: all routes are under `/api/v1/`. New incompatible changes go under `/api/v2/` rather than modifying existing routes.
