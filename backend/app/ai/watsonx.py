"""IBM watsonx.ai / Granite explanation provider.

Sends a structured prompt to ibm/granite-3-3-8b-instruct via the
ibm-watsonx-ai SDK and returns the generated explanation text.

Configuration (all via environment variables / pydantic-settings):
  WATSONX_API_KEY      — IAM API key
  WATSONX_PROJECT_ID   — watsonx.ai project ID
  WATSONX_URL          — service endpoint (default: us-south)
  WATSONX_MODEL_ID     — model to use (default: ibm/granite-3-3-8b-instruct)
  WATSONX_TIMEOUT_SECS — HTTP timeout in seconds (default: 30)

Graceful failure contract
─────────────────────────
Every exception raised by the SDK is caught here.  The caller always
receives an ExplanationResult — never an unhandled exception.
"""
from __future__ import annotations

import logging

from app.ai.base import AnalysisContext, ExplanationProvider, ExplanationResult
from app.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are DeployGuard's deployment-risk advisor. DeployGuard has already run \
a deterministic analysis of a software change and produced a structured risk report. \
Your job is to explain the findings to the developer in plain language.

CRITICAL RULES:
- Do NOT invent new risks, signals, or findings that are not in the report.
- Do NOT alter the risk score or severity tier.
- Clearly separate deterministic findings (from DeployGuard) from your guidance.
- Be concise and actionable. Developers read this before they deploy.
"""

_USER_PROMPT_TEMPLATE = """\
## DeployGuard Deterministic Analysis Report

Repository : {repository}
Branch     : {branch}
Commit     : {commit_sha}
Risk Score : {risk_score}/100
Severity   : {severity}
Files Changed : {total_files_changed} ({total_additions} additions, {total_deletions} deletions)

### Detected Risk Signals ({signal_count})

{signals_block}

---

Based ONLY on the findings above, provide:

1. **Deployment Risk Summary** (2-3 sentences): What is the overall deployment risk and why?

2. **Key Risk Factors** (bullet list): Explain the most important signals a developer must understand.

3. **Recommended Validation Steps** (numbered list): Concrete steps to validate before deploying.

4. **Suggested Testing Areas** (bullet list): Which areas of the system should be tested or monitored post-deploy?

Keep each section focused and practical. Do not mention risks that are not in the report above.
"""


def _build_signals_block(context: AnalysisContext) -> str:
    if not context.signals:
        return "No risk signals detected."
    lines: list[str] = []
    for s in context.signals:
        lines.append(
            f"- [{s.severity}] {s.title} (+{s.score_contribution:.0f} pts)\n"
            f"  {s.description}"
        )
    return "\n".join(lines)


def _build_user_prompt(context: AnalysisContext) -> str:
    return _USER_PROMPT_TEMPLATE.format(
        repository=context.repository,
        branch=context.branch,
        commit_sha=context.commit_sha,
        risk_score=context.risk_score,
        severity=context.severity,
        total_files_changed=context.total_files_changed,
        total_additions=context.total_additions,
        total_deletions=context.total_deletions,
        signal_count=len(context.signals),
        signals_block=_build_signals_block(context),
    )


class WatsonxGraniteProvider:
    """IBM watsonx.ai Granite explanation provider.

    Lazy-imports the ibm-watsonx-ai SDK so the rest of the application
    does not hard-depend on it.  If the SDK is missing or credentials are
    not configured, explain() returns a failed ExplanationResult.
    """

    def __init__(
        self,
        api_key: str | None = None,
        project_id: str | None = None,
        url: str | None = None,
        model_id: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self._api_key = api_key or settings.watsonx_api_key
        self._project_id = project_id or settings.watsonx_project_id
        self._url = url or settings.watsonx_url
        self._model_id = model_id or getattr(settings, "watsonx_model_id", "ibm/granite-3-3-8b-instruct")
        self._timeout = timeout or getattr(settings, "watsonx_timeout_secs", 30)

    def _is_configured(self) -> bool:
        return bool(self._api_key and self._project_id)

    def explain(self, context: AnalysisContext) -> ExplanationResult:
        """Call Granite and return an ExplanationResult.

        Never raises — all errors produce ExplanationResult(status="failed").
        """
        if not self._is_configured():
            logger.info(
                "watsonx.ai not configured (missing API key or project ID); "
                "skipping explanation for analysis %s",
                context.analysis_id,
            )
            return ExplanationResult(
                status="failed",
                error="watsonx.ai credentials not configured",
            )

        try:
            return self._call_api(context)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "watsonx.ai explanation failed for analysis %s: %s",
                context.analysis_id,
                exc,
            )
            return ExplanationResult(
                status="failed",
                error=str(exc),
            )

    def _call_api(self, context: AnalysisContext) -> ExplanationResult:
        """Perform the actual SDK call. Separated for easier mocking in tests."""
        try:
            from ibm_watsonx_ai import APIClient, Credentials  # type: ignore[import]
            from ibm_watsonx_ai.foundation_models import ModelInference  # type: ignore[import]
        except ImportError:
            return ExplanationResult(
                status="failed",
                error="ibm-watsonx-ai SDK not installed. Run: pip install ibm-watsonx-ai",
            )

        credentials = Credentials(url=self._url, api_key=self._api_key)
        client = APIClient(credentials=credentials, project_id=self._project_id)

        model = ModelInference(
            model_id=self._model_id,
            api_client=client,
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(context)},
        ]

        response = model.chat(
            messages=messages,
            params={
                "max_tokens": 800,       # chat API uses max_tokens (not max_new_tokens)
                "temperature": 0.2,
                "top_p": 0.9,
            },
        )

        # Extract text from response
        text = (
            response.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not text:
            return ExplanationResult(status="failed", error="Empty response from model")

        return ExplanationResult(status="done", text=text)


# Module-level singleton — replace in tests via dependency injection
_default_provider: WatsonxGraniteProvider | None = None


def get_default_provider() -> WatsonxGraniteProvider:
    global _default_provider
    if _default_provider is None:
        _default_provider = WatsonxGraniteProvider()
    return _default_provider


# Satisfy ExplanationProvider protocol statically
_: ExplanationProvider = WatsonxGraniteProvider()
