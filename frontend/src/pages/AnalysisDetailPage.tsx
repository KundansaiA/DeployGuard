import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Analysis } from '../types/api';
import AiExplanation from '../components/AiExplanation';

const SEVERITY_COLORS: Record<string, { bg: string; fg: string }> = {
  LOW:      { bg: '#d1fae5', fg: '#065f46' },
  MEDIUM:   { bg: '#fef9c3', fg: '#92400e' },
  HIGH:     { bg: '#fed7aa', fg: '#9a3412' },
  CRITICAL: { bg: '#fee2e2', fg: '#991b1b' },
};

function SeverityBadge({ tier }: { tier: string }) {
  const c = SEVERITY_COLORS[tier] ?? { bg: '#e5e7eb', fg: '#374151' };
  return (
    <span style={{
      backgroundColor: c.bg, color: c.fg,
      padding: '0.25em 0.75em', borderRadius: '4px',
      fontSize: '0.875rem', fontWeight: 600,
    }}>
      {tier}
    </span>
  );
}

export default function AnalysisDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.getAnalysis(id)
      .then(setAnalysis)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div style={{ padding: '2rem', fontFamily: 'system-ui' }}>Loading…</div>;
  if (error) return <div style={{ padding: '2rem', fontFamily: 'system-ui', color: '#b91c1c' }}>Error: {error}</div>;
  if (!analysis) return null;

  return (
    <div style={{ maxWidth: '800px', margin: '2rem auto', padding: '0 1rem', fontFamily: 'system-ui, sans-serif' }}>
      {/* Back link */}
      <Link to="/analyses" style={{ fontSize: '0.875rem', color: '#3b82d4' }}>
        ← All Analyses
      </Link>

      {/* Header */}
      <div style={{ marginTop: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>{analysis.repository}</h1>
            <p style={{ margin: '0.25rem 0 0', color: '#57606a', fontSize: '0.875rem' }}>
              {analysis.branch} · {analysis.commit_sha}
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <SeverityBadge tier={analysis.severity} />
            <div style={{ marginTop: '0.35rem', fontSize: '1.5rem', fontWeight: 700 }}>
              {analysis.risk_score.toFixed(0)}<span style={{ fontSize: '1rem', color: '#57606a' }}>/100</span>
            </div>
          </div>
        </div>

        {/* Change summary */}
        <div style={{
          display: 'flex', gap: '1.5rem', marginTop: '1rem',
          padding: '0.75rem 1rem', backgroundColor: '#f7f8fa',
          borderRadius: '6px', fontSize: '0.875rem', color: '#57606a',
        }}>
          <span><strong style={{ color: '#1f2328' }}>{analysis.total_files_changed}</strong> files</span>
          <span style={{ color: '#065f46' }}>+{analysis.total_additions}</span>
          <span style={{ color: '#991b1b' }}>−{analysis.total_deletions}</span>
          <span style={{ marginLeft: 'auto' }}>{new Date(analysis.created_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Risk Signals */}
      <section>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          Detected Risk Signals ({analysis.signals.length})
        </h2>

        {analysis.signals.length === 0 ? (
          <p style={{ color: '#57606a', padding: '0.75rem 0' }}>No risk signals detected.</p>
        ) : (
          analysis.signals.map(signal => (
            <div
              key={signal.id}
              style={{
                border: '1px solid #e5e7eb', borderRadius: '6px',
                padding: '0.875rem 1rem', marginBottom: '0.5rem',
                backgroundColor: '#fff',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <strong style={{ fontSize: '0.9rem' }}>{signal.title}</strong>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <SeverityBadge tier={signal.severity} />
                  <span style={{ fontSize: '0.8rem', color: '#57606a' }}>+{signal.score_contribution.toFixed(0)} pts</span>
                </div>
              </div>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#57606a' }}>{signal.description}</p>
              {signal.evidence && Object.keys(signal.evidence).length > 0 && (
                <details style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#57606a' }}>
                  <summary style={{ cursor: 'pointer' }}>Evidence</summary>
                  <pre style={{ margin: '0.5rem 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                    {JSON.stringify(signal.evidence, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          ))
        )}
      </section>

      {/* AI Explanation */}
      <AiExplanation
        analysisId={analysis.id}
        initialStatus={analysis.explanation_status}
        initialText={analysis.explanation_text}
        onRequest={api.requestExplanation}
      />
    </div>
  );
}
