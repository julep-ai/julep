"""Public model-caller adapters and composition helpers.

The execution engine owns a small, provider-neutral :class:`LlmCaller` seam.
This module contains integrations that consumers otherwise tend to rebuild in
worker glue: a LiteLLM adapter and a model fallback ladder around an arbitrary
caller.  Imports of LiteLLM remain lazy so the core package stays lightweight.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Awaitable, Callable, Mapping, Sequence
from importlib import import_module
from typing import Any, Optional, cast

from .dotctx import Reasoner
from .errors import ResilienceExhausted
from .execution.effects import LlmCaller, RunPrincipal
from .execution.llm import complete_reasoner
from .execution.llm_result import AttemptMeta, LlmResult
from .model_slugs import EFFORT_LEVELS, normalize_model_slug
from .qos import ReasonerDispatch
from .resilience import AttemptRecord, ErrorClass, OnAttempt, classify_error
from .transcript import Transcript

LiteLlmCompletion = Callable[..., Awaitable[Any]]

_DEFAULT_DISPATCH = ReasonerDispatch()
_ANTHROPIC_THINKING_BUDGETS: Mapping[str, int] = {
    "minimal": 128,
    "low": 1024,
    "medium": 2048,
    "high": 4096,
}


def _normalize_litellm_model(model: Any) -> Any:
    if not isinstance(model, str):
        return model
    normalized = model.strip()
    if not normalized:
        return model
    parsed = normalize_model_slug(normalized)
    provider, separator, remainder = parsed.model.partition(":")
    if not separator:
        return parsed.model
    remainder = remainder.lstrip("/")
    if provider == "fireworks" and remainder.startswith("accounts/"):
        provider = "fireworks_ai"
    return f"{provider}/{remainder}"


def _slug_effort(model: Any) -> Optional[str]:
    if not isinstance(model, str) or "@" not in model:
        return None
    suffix = model.rsplit("@", 1)[1].strip().lower()
    return suffix if suffix in EFFORT_LEVELS else None


def prepare_litellm_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Translate Julep model slugs and reasoning controls for LiteLLM.

    The mapping is deliberately pure and public so eval runners and workers use
    the same provider payload contract.  An ``@effort`` model suffix wins over
    an explicit ``reasoning_effort`` field, matching model override precedence.
    """

    prepared = dict(payload)
    raw_model = prepared.get("model")
    model = _normalize_litellm_model(raw_model)
    if model is not None:
        prepared["model"] = model

    explicit = prepared.get("reasoning_effort")
    explicit_effort = (
        explicit.strip().lower() if isinstance(explicit, str) and explicit.strip() else None
    )
    effort = _slug_effort(raw_model) or explicit_effort

    if (
        effort is not None
        and isinstance(model, str)
        and model.lower().startswith("openai/gpt-5")
        and prepared.get("temperature") not in (None, 1, 1.0)
    ):
        prepared["temperature"] = 1.0

    if effort is None:
        prepared.pop("reasoning_effort", None)
        return prepared

    if isinstance(model, str) and model.startswith("openrouter/"):
        raw_extra = prepared.get("extra_body")
        extra = dict(raw_extra) if isinstance(raw_extra, Mapping) else {}
        raw_reasoning = extra.get("reasoning")
        reasoning = dict(raw_reasoning) if isinstance(raw_reasoning, Mapping) else {}
        reasoning["effort"] = effort
        extra["reasoning"] = reasoning
        prepared["extra_body"] = extra
        prepared.pop("reasoning_effort", None)
        return prepared

    if isinstance(model, str) and model.startswith("anthropic/"):
        prepared.pop("reasoning_effort", None)
        if model.lower().startswith("anthropic/claude-opus-4-7"):
            prepared.pop("temperature", None)
            prepared.pop("top_p", None)
            prepared.pop("top_k", None)
            if effort == "none":
                return prepared
            output = prepared.get("output_config")
            output_config = dict(output) if isinstance(output, Mapping) else {}
            output_config["effort"] = "low" if effort == "minimal" else effort
            prepared["thinking"] = {"type": "adaptive"}
            prepared["output_config"] = output_config
            return prepared
        budget = _ANTHROPIC_THINKING_BUDGETS.get(effort)
        if budget is not None:
            prepared["temperature"] = 1.0
            prepared["thinking"] = {"type": "enabled", "budget_tokens": budget}
        return prepared

    prepared["reasoning_effort"] = effort
    raw_allowed = prepared.get("allowed_openai_params")
    allowed = list(raw_allowed) if isinstance(raw_allowed, list) else []
    if "reasoning_effort" not in allowed:
        allowed.append("reasoning_effort")
    prepared["allowed_openai_params"] = allowed
    return prepared


def litellm_caller(
    *,
    request_timeout_s: Optional[float] = None,
    acompletion: Optional[LiteLlmCompletion] = None,
) -> LlmCaller:
    """Return Julep's canonical five-argument caller backed by LiteLLM.

    ``acompletion`` is injectable for tests.  When omitted, ``litellm`` is
    imported on the first model call and a clear install hint is raised if the
    optional dependency is unavailable.
    """

    async def completion(
        *,
        provider: str,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> Any:
        backend = acompletion
        if backend is None:
            try:
                litellm = import_module("litellm")
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise ImportError(
                    "litellm_caller requires LiteLLM; install 'julep[litellm]'"
                ) from exc
            backend = cast(LiteLlmCompletion, vars(litellm)["acompletion"])
        payload: dict[str, Any] = {
            "model": f"{provider}:{model}",
            "messages": messages,
            **kwargs,
        }
        if request_timeout_s is not None:
            payload["timeout"] = request_timeout_s
        return await backend(**prepare_litellm_payload(payload))

    async def caller(
        reasoner: Reasoner,
        value: Any,
        principal: Optional[RunPrincipal] = None,
        transcript: Optional[Transcript] = None,
        dispatch: ReasonerDispatch = _DEFAULT_DISPATCH,
        *,
        tools: Optional[list[dict[str, Any]]] = None,
        parallel_tool_calls: Optional[bool] = None,
    ) -> Any:
        del principal  # Provider credentials are resolved by LiteLLM itself.
        # ``complete_reasoner`` consumes canonical ``provider:model`` slugs.
        # Normalize slash-form dotctx inputs before its provider split so
        # ``openai/gpt-*`` cannot fall through to the Anthropic default.
        parsed_model = normalize_model_slug(reasoner.model)
        normalized_reasoner = reasoner.replace(
            model=parsed_model.model,
            reasoning_effort=(
                parsed_model.reasoning_effort or reasoner.reasoning_effort
            ),
        )
        return await complete_reasoner(
            normalized_reasoner,
            value,
            acompletion=completion,
            transcript=transcript,  # type: ignore[arg-type]
            dispatch=dispatch,
            tools=tools,
            parallel_tool_calls=parallel_tool_calls,
        )

    return caller


def _provider(model: str) -> str:
    normalized = normalize_model_slug(model).model
    return normalized.split(":", 1)[0] if ":" in normalized else ""


def _reasoner_for_model(reasoner: Reasoner, model: str) -> Reasoner:
    parsed = normalize_model_slug(model)
    base = normalize_model_slug(reasoner.model)
    effort = (
        parsed.reasoning_effort
        or base.reasoning_effort
        or reasoner.reasoning_effort
    )
    return reasoner.replace(model=parsed.model, reasoning_effort=effort)


def with_model_ladder(
    caller: LlmCaller,
    *,
    models: Sequence[str],
    classify: Callable[[BaseException], ErrorClass] = classify_error,
    on_attempt: Optional[OnAttempt] = None,
) -> LlmCaller:
    """Wrap a caller with ordered provider-transient model failover.

    The reasoner's primary model is always attempted first, followed by
    ``models`` with stable de-duplication.  Only transient and timeout failures
    advance the ladder.  Configuration and model-behavior failures remain loud
    on the model that produced them.
    """

    async def wrapped(
        reasoner: Reasoner,
        value: Any,
        principal: Optional[RunPrincipal] = None,
        transcript: Optional[Transcript] = None,
        dispatch: ReasonerDispatch = _DEFAULT_DISPATCH,
        *,
        tools: Optional[list[dict[str, Any]]] = None,
        parallel_tool_calls: Optional[bool] = None,
    ) -> Any:
        candidates: list[Reasoner] = []
        seen_candidates: set[tuple[str, Optional[str]]] = set()
        for candidate in (reasoner.model, *models):
            normalized = _reasoner_for_model(reasoner, candidate)
            identity = (normalized.model, normalized.reasoning_effort)
            if identity not in seen_candidates:
                seen_candidates.add(identity)
                candidates.append(normalized)
        attempts: list[AttemptRecord] = []
        last_exc: Optional[Exception] = None
        for attempt_reasoner in candidates:
            provider = _provider(attempt_reasoner.model)
            try:
                extra: dict[str, Any] = {}
                if tools is not None:
                    extra["tools"] = tools
                if parallel_tool_calls is not None:
                    extra["parallel_tool_calls"] = parallel_tool_calls
                result = await cast(Any, caller)(
                    attempt_reasoner,
                    value,
                    principal,
                    transcript,
                    dispatch,
                    **extra,
                )
            except Exception as exc:
                error_class = classify(exc)
                record = AttemptRecord(
                    model=attempt_reasoner.model,
                    provider=provider,
                    outcome=error_class.value,
                    detail=str(exc),
                )
                attempts.append(record)
                if on_attempt is not None:
                    on_attempt(record)
                if error_class not in (ErrorClass.TRANSIENT, ErrorClass.TIMEOUT):
                    raise
                last_exc = exc
                continue

            record = AttemptRecord(
                model=attempt_reasoner.model,
                provider=provider,
                outcome="ok",
            )
            attempts.append(record)
            if on_attempt is not None:
                on_attempt(record)
            if isinstance(result, LlmResult):
                ladder_attempts = tuple(
                    AttemptMeta(model=item.model, provider=item.provider, outcome=item.outcome)
                    for item in attempts
                )
                return LlmResult(
                    reply=result.reply,
                    meta=dataclasses.replace(result.meta, attempts=ladder_attempts),
                )
            return result

        exhausted = ResilienceExhausted(attempts)
        if last_exc is not None:
            raise exhausted from last_exc
        raise exhausted

    return wrapped


__all__ = [
    "LiteLlmCompletion",
    "litellm_caller",
    "prepare_litellm_payload",
    "with_model_ladder",
]
