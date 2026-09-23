# AGENTS.md — Ask Mode

This file provides guidance to agents when working with code in this repository.

## Documentation Context (Non-Obvious)

- The canonical architecture reference is `docs/architecture.md` — the README is a summary only.
- `backend/app/analyzers/` is the right place to look for what risk types DeployGuard can detect.
- `backend/app/engine/` contains the scoring algorithm — that is where to look for how the 0–100 score is computed.
- The AI explanation layer (`backend/app/ai/`) is entirely decoupled from scoring; questions about "how does DeployGuard decide?" should point to the analyzers and engine, not the AI module.
- Pydantic schemas in `backend/app/schemas/` define the public API contract — they are the ground truth for what the API accepts and returns.
