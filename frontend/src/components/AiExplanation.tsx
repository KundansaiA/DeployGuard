/**
 * AiExplanation — displays the AI-generated explanation section on an analysis.
 *
 * States handled:
 *   none     — explanation not yet requested (shows a "Request" button)
 *   loading  — request in flight
 *   done     — explanation text available
 *   failed   — provider unavailable or error
 */
import React, { useState } from 'react';
import type { ExplanationStatus } from '../types/api';

interface Props {
  analysisId: string;
  initialStatus: ExplanationStatus;
  initialText: string | null;
  onRequest: (analysisId: string) => Promise<{ status: ExplanationStatus; text: string | null }>;
}

const STATUS_LABELS: Record<ExplanationStatus, string> = {
  none: 'Not generated',
  pending: 'Generating…',
  done: 'Available',
  failed: 'Unavailable',
};

const styles: Record<string, React.CSSProperties> = {
  section: {
    marginTop: '2rem',
    padding: '1.25rem 1.5rem',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    backgroundColor: '#f7f8fa',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '0.75rem',
  },
  title: {
    margin: 0,
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2328',
  },
  badge: {
    fontSize: '0.75rem',
    padding: '0.2em 0.6em',
    borderRadius: '4px',
    fontWeight: 500,
  },
  disclaimer: {
    fontSize: '0.8rem',
    color: '#57606a',
    marginBottom: '0.75rem',
    fontStyle: 'italic',
  },
  text: {
    fontSize: '0.9rem',
    lineHeight: 1.7,
    color: '#1f2328',
    whiteSpace: 'pre-wrap',
    margin: 0,
  },
  button: {
    padding: '0.5rem 1rem',
    borderRadius: '6px',
    border: '1px solid #3b82d4',
    background: '#3b82d4',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '0.875rem',
  },
  errorBox: {
    padding: '0.75rem 1rem',
    border: '1px solid #f87171',
    borderRadius: '6px',
    backgroundColor: '#fef2f2',
    color: '#b91c1c',
    fontSize: '0.875rem',
  },
  loadingBox: {
    padding: '0.75rem',
    color: '#57606a',
    fontSize: '0.875rem',
  },
};

function badgeStyle(status: ExplanationStatus): React.CSSProperties {
  const colors: Record<ExplanationStatus, { bg: string; fg: string }> = {
    none: { bg: '#e5e7eb', fg: '#57606a' },
    pending: { bg: '#fef9c3', fg: '#92400e' },
    done: { bg: '#d1fae5', fg: '#065f46' },
    failed: { bg: '#fee2e2', fg: '#991b1b' },
  };
  return {
    ...styles.badge,
    backgroundColor: colors[status].bg,
    color: colors[status].fg,
  };
}

export default function AiExplanation({ analysisId, initialStatus, initialText, onRequest }: Props) {
  const [status, setStatus] = useState<ExplanationStatus>(initialStatus);
  const [text, setText] = useState<string | null>(initialText);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRequest = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await onRequest(analysisId);
      setStatus(result.status);
      setText(result.text);
      if (result.status === 'failed') {
        setError('The AI explanation service is currently unavailable. The deterministic analysis above is unaffected.');
      }
    } catch (err) {
      setStatus('failed');
      setError(err instanceof Error ? err.message : 'Unknown error requesting explanation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section style={styles.section} aria-label="AI Explanation">
      <div style={styles.header}>
        <h2 style={styles.title}>AI Explanation</h2>
        <span style={badgeStyle(status)} title={`Status: ${status}`}>
          {STATUS_LABELS[status]}
        </span>
        <span style={{ fontSize: '0.75rem', color: '#57606a', marginLeft: 'auto' }}>
          Powered by IBM Granite
        </span>
      </div>

      <p style={styles.disclaimer}>
        ⚠ This section contains <strong>AI-generated guidance</strong> based on DeployGuard's
        deterministic findings. It does not alter the risk score or signals above.
        Always validate with your own testing before deploying.
      </p>

      {status === 'none' && !loading && (
        <button style={styles.button} onClick={handleRequest} data-testid="request-explanation-btn">
          Request AI Explanation
        </button>
      )}

      {loading && (
        <div style={styles.loadingBox} role="status" aria-live="polite">
          Generating explanation via IBM watsonx.ai…
        </div>
      )}

      {status === 'failed' && !loading && (
        <div style={styles.errorBox} role="alert">
          {error ?? 'AI explanation is currently unavailable. The deterministic analysis above is unaffected.'}
          <button
            style={{ ...styles.button, marginTop: '0.75rem', display: 'block' }}
            onClick={handleRequest}
          >
            Retry
          </button>
        </div>
      )}

      {status === 'done' && text && (
        <pre style={styles.text} data-testid="explanation-text">
          {text}
        </pre>
      )}
    </section>
  );
}
