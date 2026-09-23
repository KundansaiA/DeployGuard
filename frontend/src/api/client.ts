/**
 * Typed API client.
 * All fetch calls go through here — components never call fetch directly.
 *
 * API base URL resolution:
 *   - Production build: set VITE_API_URL at build time, e.g.
 *       VITE_API_URL=https://api.yourdomain.com/api/v1
 *   - Local dev (npm run dev): VITE_API_URL is empty, falls back to '/api/v1'
 *     which is proxied to http://localhost:8000 by vite.config.ts.
 */
import type { Analysis, AnalysisListResponse, ExplanationResponse } from '../types/api';

// VITE_API_URL must NOT have a trailing slash.
// In local dev it is undefined/empty and the Vite proxy handles /api/* → localhost:8000.
const BASE = import.meta.env.VITE_API_URL || '/api/v1';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail?.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  /** List analyses (paginated). */
  listAnalyses: (skip = 0, limit = 20): Promise<AnalysisListResponse> =>
    request(`/analyses?skip=${skip}&limit=${limit}`),

  /** Retrieve a single analysis by ID. */
  getAnalysis: (id: string): Promise<Analysis> =>
    request(`/analyses/${id}`),

  /** Get explanation status/text without triggering generation. */
  getExplanation: (analysisId: string): Promise<ExplanationResponse> =>
    request(`/analyses/${analysisId}/explanation`),

  /** Request (or return cached) AI explanation for an analysis. */
  requestExplanation: (analysisId: string): Promise<ExplanationResponse> =>
    request(`/analyses/${analysisId}/explanation`, { method: 'POST' }),
};
