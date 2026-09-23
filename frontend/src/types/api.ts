/** Shared API types — mirror backend Pydantic schemas. */

export type SeverityTier = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ExplanationStatus = 'none' | 'pending' | 'done' | 'failed';

export interface RiskSignal {
  id: string;
  signal_type: string;
  severity: SeverityTier;
  title: string;
  description: string;
  evidence: Record<string, unknown> | null;
  score_contribution: number;
  source_analyzer: string;
}

export interface Analysis {
  id: string;
  repository: string;
  branch: string;
  commit_sha: string;
  total_files_changed: number;
  total_additions: number;
  total_deletions: number;
  risk_score: number;
  severity: SeverityTier;
  explanation_text: string | null;
  explanation_status: ExplanationStatus;
  created_at: string;
  signals: RiskSignal[];
}

export interface AnalysisListResponse {
  items: Analysis[];
  total: number;
}

export interface ExplanationResponse {
  status: ExplanationStatus;
  text: string | null;
}
