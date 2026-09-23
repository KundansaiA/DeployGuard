# Tests

Cross-layer tests for DeployGuard.

| Directory | Purpose |
|---|---|
| `integration/` | Tests that exercise multiple layers together (API + DB, etc.) |
| `e2e/` | End-to-end browser tests (Playwright — future) |

Unit tests live alongside the code they test:
- Backend unit tests → `backend/tests/`
- Frontend unit tests → `frontend/src/__tests__/`
