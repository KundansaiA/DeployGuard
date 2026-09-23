import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Analysis } from '../types/api';

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
      padding: '0.2em 0.6em', borderRadius: '4px',
      fontSize: '0.75rem', fontWeight: 600,
    }}>
      {tier}
    </span>
  );
}

export default function AnalysisListPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listAnalyses(0, 50)
      .then(res => { setAnalyses(res.items); setTotal(res.total); })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ maxWidth: '800px', margin: '2rem auto', padding: '0 1rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>DeployGuard</h1>
      <p style={{ color: '#57606a', marginBottom: '1.5rem' }}>
        {total} analysis{total !== 1 ? 'es' : ''} on record
      </p>

      {loading && <p>Loading…</p>}
      {error && <p style={{ color: '#b91c1c' }}>Error: {error}</p>}

      {!loading && !error && analyses.length === 0 && (
        <p style={{ color: '#57606a' }}>No analyses yet. Submit a change via the API to get started.</p>
      )}

      {analyses.map(a => (
        <Link
          key={a.id}
          to={`/analyses/${a.id}`}
          style={{ textDecoration: 'none', color: 'inherit' }}
        >
          <div style={{
            border: '1px solid #e5e7eb', borderRadius: '8px',
            padding: '1rem 1.25rem', marginBottom: '0.75rem',
            backgroundColor: '#fff',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <strong>{a.repository}</strong>
                <span style={{ color: '#57606a', marginLeft: '0.5rem', fontSize: '0.875rem' }}>
                  {a.branch} · {a.commit_sha.slice(0, 8)}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <SeverityBadge tier={a.severity} />
                <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                  {a.risk_score.toFixed(0)}/100
                </span>
              </div>
            </div>
            <div style={{ marginTop: '0.4rem', fontSize: '0.8rem', color: '#57606a' }}>
              {a.signals.length} signal{a.signals.length !== 1 ? 's' : ''} ·{' '}
              {new Date(a.created_at).toLocaleString()}
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
