"""The first real, multi-provider ``LlmCaller`` — backed by any-llm.

The framework already routes every model call through one injectable seam; this
module fills it with a caller that dispatches to any provider any-llm supports.
Two factories expose the same core under the two seam shapes in the codebase:

* :func:`make_llm_caller` — the activity seam (``activities.py``):
  ``(Brain, value, principal, transcript) -> reply``, the canonical 4-arg
  ``LlmCaller``. Wire it via ``start_worker(llm=...)``.
* :func:`make_local_brain` — the facade seam (``agent.py``):
  ``(brain_name, payload) -> reply``. Wire it via ``Agent(..., llm=...)``; it
  resolves the registered :class:`~composable_agents.dotctx.Brain` by name to
  recover ``system`` + ``reply_schema``.

Provider selection rides on ``Brain.model``: a ``"provider:model"`` prefix picks
the provider (``"openai:gpt-4o"``); a bare slug (``"claude-opus-4-8"``) falls back
to ``default_provider``. The fallback is adapter-only, so existing brains and
their deploy goldens are byte-for-byte unchanged.

``reply_schema`` is honored with OpenAI-style ``response_format`` when the provider
supports it (any-llm converts per provider); for providers any-llm cannot convert
yet — and as a safety net when a native attempt raises — the schema is injected
into the system prompt and the JSON reply is parsed tolerantly. The parsed value
is exactly what ``interpret_brain_reply`` / ``compilePlan`` already consume.

any-llm is imported lazily, so this module loads without it. Install
``composable-agents[providers]`` plus your provider extra, e.g.
``pip install 'any-llm-sdk[anthropic,openai]'``.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
from collections.abc import Awaitable, Callable
from typing import Any, Optional

from ..dotctx import Brain, get_brain
from ..errors import ResilienceExhausted
from ..prompt import rendered_brain_for, rendered_user_for
from ..resilience import (
    AttemptRecord,
    CircuitBreaker,
    ErrorClass,
    OnAttempt,
    ResiliencePolicy,
    classify_error,
)

# any-llm's ``acompletion``-shaped callable: keyword-driven, returns an
# OpenAI-typed completion (``.choices[0].message.{content,parsed}``).
AnyCompletion = Callable[..., Awaitable[Any]]

DEFAULT_PROVIDER = "anthropic"

# Providers whose ``response_format`` conversion any-llm does not cover yet; send
# them prompt-injected JSON instead of a native structured request.
# (mozilla-ai/any-llm issues #541 gemini, #542 xai.)
_PROMPT_FALLBACK_PROVIDERS = frozenset({"gemini", "xai"})


# --------------------------------------------------------------------------- #
# Pure helpers.
# --------------------------------------------------------------------------- #
def _split_model(model: str, default_provider: str) -> tuple[str, str]:
    """``"provider:model"`` -> ``(provider, model)``; bare slug -> default."""
    provider, sep, rest = model.partition(":")
    if sep:
        return provider, rest
    return default_provider, model


def _strip_code_fence(text: str) -> str:
    """Drop a leading ```` ```json ```` / ```` ``` ```` fence and its closer."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    newline = stripped.find("\n")
    if newline != -1:
        stripped = stripped[newline + 1 :]
    if stripped.rstrip().endswith("```"):
        stripped = stripped.rstrip()[:-3]
    return stripped.strip()


def _response_format(schema: dict[str, Any]) -> dict[str, Any]:
    """OpenAI-style ``response_format``; any-llm converts it per provider."""
    return {
        "type": "json_schema",
        "json_schema": {"name": "reply", "schema": schema, "strict": False},
    }


def _ref_label(ref: Optional[dict[str, Any]]) -> str:
    if not ref:
        return ""
    if ref.get("kind") == "mcp":
        return f"{ref.get('server')}/{ref.get('tool')}"
    if ref.get("kind") == "sub":
        return f"sub:{ref.get('ref')}"
    return str(ref.get("name", ""))


def _transcript_messages(transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map neutral transcript turns to provider messages (reference mapping).

    Assistant action turns render as assistant text and tool results as
    user-visible text — replayed turns carry no provider tool-call ids, so
    the OpenAI-style ``tool`` role cannot be used. System turns (the elision
    marker / running summary) pass through as system messages.
    """
    out: list[dict[str, Any]] = []
    for turn in transcript:
        role = turn.get("role", "user")
        content = turn.get("content")
        text = content if isinstance(content, str) else json.dumps(content, sort_keys=True)
        label = _ref_label(turn.get("ref"))
        if role == "assistant" and label:
            text = f"[called {label}]" if content is None else f"[called {label}] {text}"
            out.append({"role": "assistant", "content": text})
        elif role == "tool":
            prefix = f"[{label} result] " if label else "[tool result] "
            out.append({"role": "user", "content": prefix + text})
        elif role in ("system", "user", "assistant"):
            out.append({"role": role, "content": text})
        else:
            out.append({"role": "user", "content": text})
    return out


def _messages(
    system: str,
    value: Any,
    *,
    schema_hint: Optional[dict[str, Any]],
    user_text: Optional[str] = None,
    transcript: Optional[list[dict[str, Any]]] = None,
) -> list[dict[str, Any]]:
    """System (optionally with an injected schema block), the materialized
    transcript turns when given, then the user turn: a rendered ``user_text``
    when given, else the value as a user turn."""
    system_text = system or ""
    if schema_hint is not None:
        block = (
            "Reply with a single JSON object matching this JSON Schema "
            "(no prose, no markdown fences):\n" + json.dumps(schema_hint)
        )
        system_text = f"{system_text}\n\n{block}" if system_text else block

    messages: list[dict[str, Any]] = []
    if system_text:
        messages.append({"role": "system", "content": system_text})
    if transcript:
        messages.extend(_transcript_messages(transcript))
    if user_text is not None:
        user = user_text
    else:
        user = value if isinstance(value, str) else json.dumps(value)
    messages.append({"role": "user", "content": user})
    return messages


def _parse_reply(completion: Any, *, expect_json: bool) -> Any:
    """Extract the reply: a parsed object if present, else (JSON) content text."""
    message = completion.choices[0].message
    parsed = getattr(message, "parsed", None)
    if parsed is not None:
        if isinstance(parsed, dict):
            return parsed
        dump = getattr(parsed, "model_dump", None)
        return dump() if callable(dump) else parsed

    content = message.content
    if not expect_json:
        return content
    if not isinstance(content, str):
        return content
    try:
        return json.loads(_strip_code_fence(content))
    except (json.JSONDecodeError, ValueError):
        # Hand the raw text back; interpret_brain_reply(strict) turns a
        # non-conforming reply into a clean controller_error.
        return content


# --------------------------------------------------------------------------- #
# Core.
# --------------------------------------------------------------------------- #
async def complete_brain(
    brain: Brain,
    value: Any,
    *,
    acompletion: AnyCompletion,
    default_provider: str = DEFAULT_PROVIDER,
    transcript: Optional[list[dict[str, Any]]] = None,
) -> Any:
    """One model call for ``brain`` against ``value``, returning its parsed reply.

    ``transcript`` is the materialized neutral turn list for transcript-scoped
    app rounds (agent-transcripts design); it renders as provider messages
    between the system prompt and the user turn."""
    # Render named system/user templates here so both seams (activity + facade)
    # see the same strings; already-rendered brains pass through unchanged.
    brain = rendered_brain_for(brain, value)
    user_text = rendered_user_for(brain, value)
    provider, model = _split_model(brain.model, default_provider)
    schema = brain.reply_schema

    async def call(*, native: bool) -> Any:
        if native and schema is not None:
            messages = _messages(
                brain.system, value,
                schema_hint=None, user_text=user_text, transcript=transcript,
            )
            kwargs: dict[str, Any] = {"response_format": _response_format(schema)}
        else:
            messages = _messages(
                brain.system, value,
                schema_hint=schema, user_text=user_text, transcript=transcript,
            )
            kwargs = {}
        if brain.temperature is not None:
            kwargs["temperature"] = brain.temperature
        if brain.max_tokens is not None:
            kwargs["max_tokens"] = brain.max_tokens
        return await acompletion(provider=provider, model=model, messages=messages, **kwargs)

    if schema is not None and provider not in _PROMPT_FALLBACK_PROVIDERS:
        try:
            completion = await call(native=True)
        except Exception:
            # Provider/any-llm could not honor response_format; reissue the round
            # with the schema injected into the prompt instead.
            completion = await call(native=False)
    else:
        completion = await call(native=False)

    return _parse_reply(completion, expect_json=schema is not None)


def _resolve_acompletion(acompletion: Optional[AnyCompletion]) -> AnyCompletion:
    if acompletion is not None:
        return acompletion
    try:
        from any_llm import acompletion as any_llm_acompletion
    except ImportError as exc:  # pragma: no cover - exercised only without any-llm
        raise ImportError(
            "any-llm is required for the provider LLM caller; install "
            "composable-agents[providers] plus your provider extra "
            "(e.g. pip install 'any-llm-sdk[anthropic,openai]')."
        ) from exc
    return any_llm_acompletion


# --------------------------------------------------------------------------- #
# Seam factories.
# --------------------------------------------------------------------------- #
def make_llm_caller(
    *,
    default_provider: str = DEFAULT_PROVIDER,
    acompletion: Optional[AnyCompletion] = None,
) -> Callable[..., Awaitable[Any]]:
    """Activity-seam ``LlmCaller``: ``(Brain, value, principal, transcript) -> reply``.

    The canonical 4-argument caller form: the principal is accepted (this
    caller resolves no per-tenant credentials itself) and the transcript is
    rendered into provider messages. Pass ``acompletion`` to inject a client
    (tests); otherwise any-llm's is imported lazily on first call.
    """

    async def caller(
        brain: Brain,
        value: Any,
        principal: Optional[dict[str, Any]] = None,
        transcript: Optional[list[dict[str, Any]]] = None,
    ) -> Any:
        return await complete_brain(
            brain, value,
            acompletion=_resolve_acompletion(acompletion),
            default_provider=default_provider,
            transcript=transcript,
        )

    return caller


def make_local_brain(
    *,
    default_provider: str = DEFAULT_PROVIDER,
    acompletion: Optional[AnyCompletion] = None,
) -> Callable[[str, Any], Awaitable[Any]]:
    """Facade-seam llm: ``(brain_name, payload) -> reply``.

    Resolves the registered :class:`Brain` by name (the facade passes the brain
    name) to recover ``model`` / ``system`` / ``reply_schema``.
    """

    async def caller(brain_name: str, payload: Any) -> Any:
        return await complete_brain(
            get_brain(brain_name),
            payload,
            acompletion=_resolve_acompletion(acompletion),
            default_provider=default_provider,
        )

    return caller


# --------------------------------------------------------------------------- #
# Resilient caller: deterministic fallback + circuit breaker around the core.
# --------------------------------------------------------------------------- #
def _with_model(brain: Brain, model: str) -> Brain:
    """A copy of ``brain`` addressed at a different model (not re-registered)."""
    if model == brain.model:
        return brain
    return dataclasses.replace(brain, model=model)


def make_resilient_llm_caller(
    *,
    policy: ResiliencePolicy,
    breaker: Optional[CircuitBreaker] = None,
    on_attempt: Optional[OnAttempt] = None,
    classifier: Callable[[BaseException], ErrorClass] = classify_error,
    default_provider: str = DEFAULT_PROVIDER,
    acompletion: Optional[AnyCompletion] = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> Callable[..., Awaitable[Any]]:
    """An ``LlmCaller`` that survives provider outages deterministically.

    Walks ``policy.candidates(brain.model)`` strictly in order. Per candidate:

    * an open circuit for the candidate's provider skips it (recorded, never
      silent);
    * TRANSIENT/TIMEOUT failures charge the breaker and retry the same model up
      to the policy's per-class budget (with backoff), then advance;
    * a CONFIG failure (bad key, unknown model, malformed request) re-raises
      immediately — a fallback must never mask misconfiguration;
    * when ``brain.reply_schema`` is set and the reply did not parse into a
      JSON object, that is MODEL_BEHAVIOR: advance to the next model without
      charging the breaker (the provider answered; the model misbehaved).

    Every attempt is reported through ``on_attempt`` (an
    :class:`~composable_agents.resilience.AttemptRecord`) so workers can feed
    projection sinks / OTel with which model actually served. Providers whose
    SDKs wrap errors in custom hierarchies can swap ``classifier`` for their
    own ``exception -> ErrorClass`` mapping. When the chain is
    exhausted, raises :class:`~composable_agents.errors.ResilienceExhausted`
    carrying the full attempt log.

    On Temporal, pair this with ``ExecutionPolicy(brain_max_attempts=1)`` so the
    engine's blind ``invokeBrain`` retries do not multiply the ladder; on DBOS
    brain steps never retry, so this caller is the whole story by design.
    """

    def _notify(record: AttemptRecord) -> None:
        if on_attempt is not None:
            on_attempt(record)

    async def caller(
        brain: Brain,
        value: Any,
        principal: Optional[dict[str, Any]] = None,
        transcript: Optional[list[dict[str, Any]]] = None,
    ) -> Any:
        resolved = _resolve_acompletion(acompletion)
        attempts: list[AttemptRecord] = []
        last_exc: Optional[Exception] = None

        for model in policy.candidates(brain.model):
            provider, _ = _split_model(model, default_provider)
            if breaker is not None and not breaker.allow(provider):
                record = AttemptRecord(
                    model=model,
                    provider=provider,
                    outcome="skipped_open_circuit",
                    detail=f"circuit open for provider {provider!r}",
                )
                attempts.append(record)
                _notify(record)
                continue

            candidate = _with_model(brain, model)
            attempt = 0
            while True:
                try:
                    reply = await complete_brain(
                        candidate, value,
                        acompletion=resolved, default_provider=default_provider,
                        transcript=transcript,
                    )
                except Exception as exc:
                    error_class = classifier(exc)
                    record = AttemptRecord(
                        model=model, provider=provider,
                        outcome=error_class.value, detail=str(exc),
                    )
                    attempts.append(record)
                    _notify(record)
                    if error_class is ErrorClass.CONFIG:
                        raise
                    last_exc = exc
                    if breaker is not None:
                        breaker.record_failure(provider)
                    attempt += 1
                    if attempt < policy.attempts_for(error_class):
                        # A failure can open the circuit mid-candidate: stop
                        # hammering the provider, advance down the chain.
                        if breaker is not None and not breaker.allow(provider):
                            break
                        await sleep(policy.backoff_s(attempt - 1))
                        continue
                    break  # candidate exhausted; advance down the chain

                if breaker is not None:
                    breaker.record_success(provider)
                if brain.reply_schema is not None and not isinstance(reply, dict):
                    record = AttemptRecord(
                        model=model, provider=provider,
                        outcome=ErrorClass.MODEL_BEHAVIOR.value,
                        detail="reply did not parse into a JSON object",
                    )
                    attempts.append(record)
                    _notify(record)
                    break  # model misbehaved; the provider is healthy
                record = AttemptRecord(model=model, provider=provider, outcome="ok")
                attempts.append(record)
                _notify(record)
                return reply

        raise ResilienceExhausted(attempts) from last_exc

    return caller


__all__ = [
    "AnyCompletion",
    "DEFAULT_PROVIDER",
    "complete_brain",
    "make_llm_caller",
    "make_local_brain",
    "make_resilient_llm_caller",
]
