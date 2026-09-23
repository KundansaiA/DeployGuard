/**
 * Tests for the AiExplanation component.
 * All external API calls are mocked — no real network needed.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AiExplanation from '../components/AiExplanation';
import type { ExplanationStatus } from '../types/api';

const ANALYSIS_ID = 'test-analysis-001';
const EXPLANATION_TEXT = '## Deployment Risk Summary\nHigh risk due to auth changes.';

function renderComponent(
  status: ExplanationStatus,
  text: string | null,
  onRequest = vi.fn(),
) {
  return render(
    <AiExplanation
      analysisId={ANALYSIS_ID}
      initialStatus={status}
      initialText={text}
      onRequest={onRequest}
    />,
  );
}

describe('AiExplanation', () => {
  describe('none state', () => {
    it('shows "Request AI Explanation" button', () => {
      renderComponent('none', null);
      expect(screen.getByTestId('request-explanation-btn')).toBeInTheDocument();
    });

    it('does not show explanation text', () => {
      renderComponent('none', null);
      expect(screen.queryByTestId('explanation-text')).toBeNull();
    });

    it('shows disclaimer about AI-generated content', () => {
      renderComponent('none', null);
      expect(screen.getByText(/AI-generated guidance/i)).toBeInTheDocument();
    });
  });

  describe('successful explanation', () => {
    it('shows explanation text after successful request', async () => {
      const mockRequest = vi.fn().mockResolvedValue({
        status: 'done' as ExplanationStatus,
        text: EXPLANATION_TEXT,
      });

      renderComponent('none', null, mockRequest);
      fireEvent.click(screen.getByTestId('request-explanation-btn'));

      await waitFor(() => {
        expect(screen.getByTestId('explanation-text')).toBeInTheDocument();
      });

      expect(screen.getByTestId('explanation-text').textContent).toBe(EXPLANATION_TEXT);
    });

    it('calls onRequest with the correct analysisId', async () => {
      const mockRequest = vi.fn().mockResolvedValue({ status: 'done', text: 'ok' });
      renderComponent('none', null, mockRequest);

      fireEvent.click(screen.getByTestId('request-explanation-btn'));
      await waitFor(() => expect(mockRequest).toHaveBeenCalledWith(ANALYSIS_ID));
    });

    it('renders pre-existing done explanation without button', () => {
      renderComponent('done', EXPLANATION_TEXT);
      expect(screen.getByTestId('explanation-text').textContent).toBe(EXPLANATION_TEXT);
      expect(screen.queryByTestId('request-explanation-btn')).toBeNull();
    });
  });

  describe('provider unavailable', () => {
    it('shows error message when provider returns failed', async () => {
      const mockRequest = vi.fn().mockResolvedValue({
        status: 'failed' as ExplanationStatus,
        text: null,
      });

      renderComponent('none', null, mockRequest);
      fireEvent.click(screen.getByTestId('request-explanation-btn'));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    it('renders initial failed state with error message', () => {
      renderComponent('failed', null);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('shows retry button on failure', async () => {
      const mockRequest = vi.fn().mockResolvedValue({ status: 'failed', text: null });
      renderComponent('none', null, mockRequest);

      fireEvent.click(screen.getByTestId('request-explanation-btn'));
      await waitFor(() => screen.getByRole('alert'));

      expect(screen.getByText(/retry/i)).toBeInTheDocument();
    });
  });

  describe('loading state', () => {
    it('shows loading indicator while request is in flight', async () => {
      // Never-resolving promise simulates in-flight request
      const mockRequest = vi.fn().mockReturnValue(new Promise(() => {}));
      renderComponent('none', null, mockRequest);

      fireEvent.click(screen.getByTestId('request-explanation-btn'));

      expect(await screen.findByRole('status')).toBeInTheDocument();
    });
  });

  describe('error state', () => {
    it('shows error when request throws', async () => {
      const mockRequest = vi.fn().mockRejectedValue(new Error('Network failure'));
      renderComponent('none', null, mockRequest);

      fireEvent.click(screen.getByTestId('request-explanation-btn'));

      await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
      expect(screen.getByRole('alert').textContent).toContain('Network failure');
    });
  });

  describe('disclaimer', () => {
    it('always shows IBM Granite attribution', () => {
      renderComponent('none', null);
      expect(screen.getByText(/IBM Granite/i)).toBeInTheDocument();
    });

    it('clarifies AI does not alter risk score', () => {
      renderComponent('none', null);
      expect(screen.getByText(/does not alter the risk score/i)).toBeInTheDocument();
    });
  });
});
