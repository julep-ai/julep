"""The first real, multi-provider ``LlmCaller`` — backed by any-llm.

The framework already routes every model call through one injectable seam; this
module fills it with a caller that dispatches to any provider any-llm supports.
Two factories expose the same core under the two seam shapes in the codebase:

* :func:`make_llm_caller` — the activity seam (``activities.py``):
  ``(Reasoner, value, principal, transcript, dispatch) -> reply``, the canonical
  ``LlmCaller``. Wire it via ``start_worker(llm=...)``.
* :func:`make_local_reasoner` — the facade seam (``agent.py``):
  ``(reasoner_name, payload) -> reply``. Wire it via ``Agent(..., llm=...)``; it
  resolves the registered :class:`~julep.dotctx.Reasoner` by name to
  recover ``system`` + ``reply_schema``.

Provider selection rides on ``Reasoner.model``: a ``"provider:model"`` prefix picks
the provider (``"openai:gpt-4o"``); a bare slug (``"claude-opus-4-8"``) falls back
to ``default_provider``. The fallback is adapter-only, so existing reasoners and
their deploy goldens are byte-for-byte unchanged.

``reply_schema`` is honored with OpenAI-style ``response_format`` when the provider
supports it (any-llm converts per provider); for providers any-llm cannot convert
yet — and as a safety net when a native attempt raises — the schema is injected
into the system prompt and the JSON reply is parsed tolerantly. The parsed value
is exactly what ``interpret_reasoner_reply`` / ``compilePlan`` already consume.
A schema-less reasoner declaring mem-mcp's ``response_format: {type: json_object}``
sends that kwarg natively through the same latch; its fallback reissues *without*
the kwarg (no prompt injection — mem-mcp prompts self-instruct JSON), recorded on
the meta, never silent. A reply schema always wins over ``json_object``.

any-llm is imported lazily, so this module loads without it. Install
``julep[providers]`` plus your provider extra, e.g.
``pip install 'any-llm-sdk[anthropic,openai]'``.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import re
import time
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Optional

from ..agent_loop import NATIVE_TOOLS_KEY, ROUND_NOTE_KEY
from ..dotctx import Reasoner, get_reasoner
from ..errors import ResilienceExhausted
from ..prompt import rendered_reasoner_for, rendered_user_for
from ..qos import ReasonerDispatch, QoSTier
from ..resilience import (
    AttemptRecord,
    CircuitBreaker,
    ErrorClass,
    OnAttempt,
    ResiliencePolicy,
    classify_error,
    is_auth_error,
)
from .llm_result import AttemptMeta, LlmCallMeta, LlmResult
from .openai_responses import (
    AnyResponses,
    ResponsesModelBehaviorError,
    ResponsesRefusalError,
    call_openai_responses,
    is_responses_result,
    parse_responses_reply,
    responses_cache_usage,
    responses_usage,
    uses_openai_responses,
)

logger = logging.getLogger(__name__)

# any-llm's ``acompletion``-shaped callable: keyword-driven, returns an
# OpenAI-typed completion (``.choices[0].message.{content,parsed}``).
AnyCompletion = Callable[..., Awaitable[Any]]

DEFAULT_PROVIDER = "anthropic"

# Providers whose ``response_format`` conversion any-llm does not cover yet; send
# them prompt-injected JSON instead of a native structured request.
# (mozilla-ai/any-llm issues #541 gemini, #542 xai.)
_PROMPT_FALLBACK_PROVIDERS = frozenset({"gemini", "xai"})
_DEFAULT_REASONER_DISPATCH = ReasonerDispatch()
_PROVIDER_SAFE_RE = re.compile(r"[^A-Za-z0-9_-]")


# --------------------------------------------------------------------------- #
# Pure helpers.
# --------------------------------------------------------------------------- #
def _split_model(model: str, default_provider: str) -> tuple[str, str]:
    """``"provider:model"`` -> ``(provider, model)``; bare slug -> default."""
    provider, sep, rest = model.partition(":")
    if sep:
        return provider, rest
    return default_provider, model


def _effort_for_provider(effort: Optional[str], provider: str) -> Optional[str]:
    """Clamp CA effort vocabulary to what the provider actually accepts.

    OpenAI's reasoning_effort scale tops out at ``xhigh``; ``max`` is
    CA/anthropic vocabulary and any-llm forwards it verbatim, so an
    ``openai:...@max`` reasoner would be a 400 without this."""
    if effort == "max" and provider == "openai":
        return "xhigh"
    return effort


def _qos_request_fields(provider: str, qos: QoSTier) -> dict[str, Any]:
    """Provider-specific QoS request kwargs for sync reasoner dispatch."""
    qos = QoSTier(qos)
    if qos is QoSTier.BATCH:
        raise ValueError("BATCH must not reach complete_reasoner")

    if provider == "openai":
        return {
            QoSTier.PRIORITY: {"service_tier": "priority"},
            QoSTier.STANDARD: {},
            QoSTier.FLEX: {"service_tier": "flex"},
        }[qos]
    if provider == "anthropic":
        return {
            QoSTier.PRIORITY: {"service_tier": "priority"},
            QoSTier.STANDARD: {},
            QoSTier.FLEX: {"service_tier": "standard_only"},
        }[qos]
    return {}


def provider_safe_tool_name(name: str) -> str:
    """Provider-safe function name for OpenAI-compatible native tool APIs."""
    safe = _PROVIDER_SAFE_RE.sub("_", name)
    return safe[:64] if len(safe) > 64 else safe


def _provider_safe_collision_name(base: str, n: int) -> str:
    suffix = f"_{n}"
    return f"{base[: 64 - len(suffix)]}{suffix}"


def provider_safe_tool_defs(
    tools: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Rewrite tool function names to provider-safe aliases.

    Returns ``(safe_tools, reverse)`` where ``reverse`` maps provider aliases
    back to the original tool keys. If no rewrite is needed, preserves the
    original list identity and returns an empty reverse map.
    """
    needs_rewrite = False
    reverse: dict[str, str] = {}
    used: set[str] = set()
    safe_tools: list[dict[str, Any]] = []
    for tool_def in tools:
        fn = tool_def.get("function", {}) if isinstance(tool_def, dict) else {}
        original = fn.get("name", "")
        safe = provider_safe_tool_name(original)
        if safe != original:
            needs_rewrite = True
        base = safe
        n = 2
        while safe in used and reverse.get(safe) != original:
            safe = _provider_safe_collision_name(base, n)
            n += 1
            needs_rewrite = True
        used.add(safe)
        if safe != original:
            reverse[safe] = original
        new_fn = {**fn, "name": safe}
        safe_tools.append({**tool_def, "function": new_fn})
    if not needs_rewrite:
        return tools, {}
    return safe_tools, reverse


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

    Assistant action turns with provider tool-call ids round-trip as native
    tool calls, and matching tool results use the OpenAI-style ``tool`` role.
    Id-less assistant action turns still render as assistant text, and id-less
    tool results still render as user-visible text. System turns (the elision
    marker / running summary) pass through as system messages.
    """
    out: list[dict[str, Any]] = []
    for turn in transcript:
        role = turn.get("role", "user")
        content = turn.get("content")
        text = content if isinstance(content, str) else json.dumps(content, sort_keys=True)
        label = _ref_label(turn.get("ref"))
        if role == "assistant" and turn.get("tool_calls"):
            calls: list[dict[str, Any]] = []
            for call in turn["tool_calls"]:
                copied = dict(call)
                function = dict(copied.get("function", {}))
                if not function.get("arguments"):
                    function["arguments"] = (
                        json.dumps(content, sort_keys=True) if content is not None else "{}"
                    )
                copied["function"] = function
                calls.append(copied)
            out.append({"role": "assistant", "content": None, "tool_calls": calls})
        elif role == "tool" and "tool_call_id" in turn:
            out.append(
                {
                    "role": "tool",
                    "tool_call_id": turn["tool_call_id"],
                    "content": text,
                }
            )
        elif role == "assistant" and label:
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
    when given, else the value as a user turn. A mapping value with a non-empty
    string under the reserved ``ROUND_NOTE_KEY`` renders that note as a
    trailing system line and omits the reserved key from the user turn."""
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
    round_note: Optional[str] = None
    if isinstance(value, Mapping):
        candidate = value.get(ROUND_NOTE_KEY)
        if isinstance(candidate, str) and candidate:
            round_note = candidate

    if user_text is not None:
        user = user_text
    elif isinstance(value, Mapping) and ROUND_NOTE_KEY in value:
        # Strip the reserved round-note key from the model-facing user JSON;
        # it is delivered as the trailing system line below, never as content.
        user = json.dumps({k: v for k, v in value.items() if k != ROUND_NOTE_KEY})
    else:
        user = value if isinstance(value, str) else json.dumps(value)
    messages.append({"role": "user", "content": user})
    if round_note is not None:
        messages.append({"role": "system", "content": round_note})
    return messages


def _prompt_cache_control(prompt_cache: str) -> dict[str, Any]:
    # "5m" => Anthropic's default ephemeral (no ttl key); "1h" => explicit ttl.
    # Any other value is a loud teaching error (G-8): never silently coerced to
    # the most-expensive 1h write. The object-first Reasoner constructor already
    # validates, this is the defense-in-depth at the wire seam.
    if prompt_cache == "5m":
        return {"type": "ephemeral"}
    if prompt_cache == "1h":
        return {"type": "ephemeral", "ttl": "1h"}
    raise ValueError(
        f"unsupported prompt_cache {prompt_cache!r}; "
        "supported values are '5m' or '1h'"
    )


def _block_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
    return "" if content is None else json.dumps(content)


def _apply_prompt_cache(
    provider: str,
    prompt_cache: Optional[str],
    messages: list[dict[str, Any]],
    kwargs: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Provider-safe Anthropic prompt-cache wiring (spike path a).

    Anthropic only: rewrite the system prefix into content blocks carrying a
    ``cache_control`` marker (stable prefix), and on transcript-bearing calls
    mark the growing-conversation tail (the final user turn) with a second
    marker. All system messages are MERGED into exactly one block-form system
    message because any-llm's anthropic completion adapter string-concatenates
    multiple system messages and would crash/corrupt on a list-content system
    block otherwise (spike finding). A trailing *volatile* system message
    (e.g. a per-round note appended after the user turn) is emitted as an
    un-cached block AFTER the cache_control breakpoint so per-round changes
    never invalidate the cached prefix; a cache breakpoint is placed on the
    system block only when a stable (pre-final-turn) prefix exists, so a sole
    trailing note carries NO cache_control. Non-anthropic providers and an
    unset ``prompt_cache`` return the inputs unchanged (recording happens on the
    meta, not here)."""
    if prompt_cache is None or provider != "anthropic":
        return messages, kwargs
    cc = _prompt_cache_control(prompt_cache)
    out = [dict(m) for m in messages]
    sys_idxs = [i for i, m in enumerate(out) if m.get("role") == "system"]
    last_non_sys = max(
        (i for i, m in enumerate(out) if m.get("role") != "system"), default=-1
    )
    if sys_idxs:
        stable = [_block_text(out[i]) for i in sys_idxs if last_non_sys == -1 or i < last_non_sys]
        volatile = [_block_text(out[i]) for i in sys_idxs if last_non_sys != -1 and i > last_non_sys]
        blocks: list[dict[str, Any]] = []
        if stable:
            blocks.append({"type": "text", "text": "\n".join(stable), "cache_control": cc})
        blocks.extend({"type": "text", "text": t} for t in volatile)
        first = sys_idxs[0]
        out[first] = {"role": "system", "content": blocks}
        drop = set(sys_idxs[1:])
        out = [m for j, m in enumerate(out) if j not in drop]
    # Growing-conversation tail marker: on transcript-bearing calls (>=2
    # non-system messages) mark the final user turn.
    non_sys = [i for i, m in enumerate(out) if m.get("role") != "system"]
    if len(non_sys) >= 2:
        for i in reversed(non_sys):
            if out[i].get("role") == "user" and isinstance(out[i].get("content"), str):
                out[i] = {
                    **out[i],
                    "content": [{"type": "text", "text": out[i]["content"], "cache_control": cc}],
                }
                break
    return out, kwargs


def _has_cache_marker(messages: list[dict[str, Any]]) -> bool:
    """True when any message carries a content block with ``cache_control``."""
    for m in messages:
        content = m.get("content")
        if isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and "cache_control" in b:
                    return True
    return False


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
        # Tool the raw text back; interpret_reasoner_reply(strict) turns a
        # non-conforming reply into a clean controller_error.
        return content


def _parse_tool_call_arguments(arguments: Any) -> Any:
    if not isinstance(arguments, str):
        return arguments
    try:
        return json.loads(arguments)
    except (json.JSONDecodeError, ValueError):
        return arguments


def _parse_completion_reply(completion: Any, *, expect_json: bool) -> tuple[Any, int]:
    """Extract native tool-call replies before falling back to text/JSON."""
    message = completion.choices[0].message
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        return {
            "tool_calls": [
                {
                    "id": getattr(tool_call, "id", None),
                    "tool": getattr(getattr(tool_call, "function", None), "name", None),
                    "input": _parse_tool_call_arguments(
                        getattr(getattr(tool_call, "function", None), "arguments", "")
                    ),
                }
                for tool_call in tool_calls
            ]
        }, len(tool_calls)
    return _parse_reply(completion, expect_json=expect_json), 0


def _add_tokens(a: int | None, b: int | None) -> int | None:
    if a is None:
        return b
    if b is None:
        return a
    return a + b


def _usage_of(completion: Any) -> tuple[int | None, int | None, int | None]:
    if is_responses_result(completion):
        return responses_usage(completion)
    usage = getattr(completion, "usage", None)
    if usage is None:
        return None, None, None
    pt = getattr(usage, "prompt_tokens", None)
    ct = getattr(usage, "completion_tokens", None)
    tt = getattr(usage, "total_tokens", None)
    if tt is None and pt is not None and ct is not None:
        tt = pt + ct
    return pt, ct, tt


def _cache_usage_of(completion: Any) -> tuple[int | None, int | None]:
    """(cache_read, cache_creation) from either anthropic-style raw usage keys
    or the OpenAI-normalized ``prompt_tokens_details.cached_tokens`` (the only
    cache field any-llm surfaces on the anthropic *completion* path)."""
    if is_responses_result(completion):
        return responses_cache_usage(completion)
    usage = getattr(completion, "usage", None)
    if usage is None:
        return None, None
    read = getattr(usage, "cache_read_input_tokens", None)
    if read is None:
        details = getattr(usage, "prompt_tokens_details", None)
        if details is not None:
            read = getattr(details, "cached_tokens", None)
    creation = getattr(usage, "cache_creation_input_tokens", None)
    return read, creation


def _served_model_of(completion: Any, fallback: str) -> str:
    m = getattr(completion, "model", None)
    if not isinstance(m, str) or not m:
        return fallback
    return m.split("/", 1)[1] if "/" in m else m


# --------------------------------------------------------------------------- #
# Core.
# --------------------------------------------------------------------------- #
async def complete_reasoner(
    reasoner: Reasoner,
    value: Any,
    *,
    acompletion: Optional[AnyCompletion] = None,
    aresponses: Optional[AnyResponses] = None,
    default_provider: str = DEFAULT_PROVIDER,
    transcript: Optional[list[dict[str, Any]]] = None,
    dispatch: ReasonerDispatch = _DEFAULT_REASONER_DISPATCH,
    tools: Optional[list[dict[str, Any]]] = None,
    parallel_tool_calls: Optional[bool] = None,
) -> LlmResult:
    """One model call for ``reasoner`` against ``value``, returning its parsed reply.

    ``transcript`` is the materialized neutral turn list for transcript-scoped
    app rounds (agent-transcripts design); it renders as provider messages
    between the system prompt and the user turn.

    ``tools`` and ``parallel_tool_calls`` pass native provider tool definitions
    through to any-llm. When tools are present, schema guidance remains prompt-
    injected and ``response_format`` is omitted from that request."""
    if dispatch.qos == QoSTier.BATCH:
        raise ValueError("BATCH must not reach complete_reasoner")

    # Render named system/user templates here so both seams (activity + facade)
    # see the same strings; already-rendered reasoners pass through unchanged.
    render_value = (
        {k: v for k, v in value.items() if k != ROUND_NOTE_KEY}
        if isinstance(value, Mapping)
        else value
    )
    reasoner = rendered_reasoner_for(reasoner, render_value)
    user_text = rendered_user_for(reasoner, render_value)
    provider, model = _split_model(reasoner.model, default_provider)
    use_responses = uses_openai_responses(provider, model)
    schema = reasoner.reply_schema
    # mem-mcp's declarative json_object mode claims the kwarg only when no
    # reply schema does (the schema path wins; the call never carries both).
    json_object = schema is None and reasoner.response_format == "json_object"
    has_tools = bool(tools)
    safe_tools, tool_name_reverse = (
        provider_safe_tool_defs(tools) if tools else (tools, {})
    )

    def _restore_tool_calls(parsed: Any) -> Any:
        if tool_name_reverse and isinstance(parsed, dict):
            calls = parsed.get("tool_calls")
            if isinstance(calls, list):
                for tool_call in calls:
                    if isinstance(tool_call, dict):
                        tool = tool_call.get("tool")
                        tool_call["tool"] = tool_name_reverse.get(tool, tool)
        return parsed

    pc_marker_placed = False

    async def call(*, native: bool, retry_note: Optional[str] = None) -> Any:
        nonlocal pc_marker_placed
        # Native tool rounds cannot carry response_format; keep schema guidance
        # in the prompt so FINISH replies can still parse on non-tool rounds.
        native_response_format = native and not has_tools
        if native_response_format and schema is not None:
            messages = _messages(
                reasoner.system, value,
                schema_hint=None, user_text=user_text, transcript=transcript,
            )
            kwargs: dict[str, Any] = {"response_format": _response_format(schema)}
        elif native_response_format and json_object:
            # No schema to inject; the prompt self-instructs JSON. The
            # non-native reissue below simply drops the kwarg. Replies stay
            # raw text either way — json_object constrains the provider, not
            # CA parsing; callers own parsing (mem-mcp's use parse_llm_json).
            messages = _messages(
                reasoner.system, value,
                schema_hint=None, user_text=user_text, transcript=transcript,
            )
            kwargs = {"response_format": {"type": "json_object"}}
        else:
            messages = _messages(
                reasoner.system, value,
                schema_hint=schema, user_text=user_text, transcript=transcript,
            )
            kwargs = {}
        if has_tools:
            kwargs["tools"] = safe_tools
            if parallel_tool_calls is not None:
                kwargs["parallel_tool_calls"] = parallel_tool_calls
        if retry_note is not None:
            messages.append({"role": "user", "content": retry_note})
        effort = reasoner.reasoning_effort
        if effort is not None:
            kwargs["reasoning_effort"] = _effort_for_provider(effort, provider)
        # Thinking modes reject or require fixed sampling params; omit
        # temperature whenever reasoning is actually enabled (mirrors mem-mcp's
        # get_temperature_for_reasoning, in provider-safe form).
        if reasoner.temperature is not None and (effort is None or effort == "none"):
            kwargs["temperature"] = reasoner.temperature
        if reasoner.max_tokens is not None:
            kwargs["max_tokens"] = reasoner.max_tokens
        kwargs.update(_qos_request_fields(provider, dispatch.qos))
        messages, kwargs = _apply_prompt_cache(
            provider, reasoner.prompt_cache, messages, kwargs
        )
        pc_marker_placed = _has_cache_marker(messages)
        if use_responses:
            return await call_openai_responses(
                _resolve_aresponses(aresponses),
                provider=provider,
                model=model,
                messages=messages,
                kwargs=kwargs,
                tool_name_aliases={
                    original: alias for alias, original in tool_name_reverse.items()
                },
            )
        return await _resolve_acompletion(acompletion)(
            provider=provider, model=model, messages=messages, **kwargs
        )

    started = time.time()
    fallback_reason: Optional[str] = None
    native_ok = True   # latched: after one response_format failure, never retry native
    retries_used = 0

    async def dispatch_once(retry_note: Optional[str] = None) -> Any:
        nonlocal fallback_reason, native_ok
        if not has_tools and (schema is not None or json_object) and native_ok \
                and provider not in _PROMPT_FALLBACK_PROVIDERS:
            try:
                return await call(native=True, retry_note=retry_note)
            except Exception as exc:
                if is_auth_error(exc):
                    raise  # auth failure — fallback must never mask it
                # Broader CONFIG (400/422) is exactly how providers reject an
                # unsupported response_format, so it falls through; a genuine
                # bad request fails the reissue identically and raises there.
                # Provider/any-llm could not honor response_format; reissue with
                # the schema injected into the prompt (json_object mode just
                # drops the kwarg) — recorded, never silent (G-8). The latch
                # records the first downgrade only and stops native re-attempts
                # on subsequent re-asks.
                native_ok = False
                fallback_reason = repr(exc)
                logger.warning(
                    "response_format fallback for %s (%s): retrying prompt-injected: %s",
                    reasoner.name, provider, fallback_reason,
                )
        return await call(native=False, retry_note=retry_note)

    completion = await dispatch_once()
    # Usage accumulates over every attempt — re-asks cost tokens too.
    pt, ct, tt = _usage_of(completion)
    cache_read, cache_creation = _cache_usage_of(completion)
    reply, native_tool_calls = (
        parse_responses_reply(completion, expect_json=schema is not None)
        if is_responses_result(completion)
        else _parse_completion_reply(completion, expect_json=schema is not None)
    )
    reply = _restore_tool_calls(reply)
    while (
        schema is not None
        and not isinstance(reply, dict)
        and retries_used < reasoner.output_retries
    ):
        retries_used += 1
        logger.warning(
            "reply for %s did not parse as JSON object; re-ask %d/%d",
            reasoner.name, retries_used, reasoner.output_retries,
        )
        completion = await dispatch_once(
            retry_note=(
                "Your previous reply was not a single valid JSON object matching "
                "the required schema. Reply again with ONLY the JSON object."
            )
        )
        apt, act, att = _usage_of(completion)
        pt, ct, tt = _add_tokens(pt, apt), _add_tokens(ct, act), _add_tokens(tt, att)
        rcr, rcc = _cache_usage_of(completion)
        cache_read = _add_tokens(cache_read, rcr)
        cache_creation = _add_tokens(cache_creation, rcc)
        reply, native_tool_calls = (
            parse_responses_reply(completion, expect_json=True)
            if is_responses_result(completion)
            else _parse_completion_reply(completion, expect_json=True)
        )
        reply = _restore_tool_calls(reply)
    ended = time.time()
    pc = reasoner.prompt_cache
    pc_requested: Optional[str]
    pc_applied: Optional[bool]
    pc_reason: Optional[str]
    if pc is None:
        pc_requested = pc_reason = None
        pc_applied = None
    elif provider == "anthropic":
        # applied reflects ACTUAL marker placement, not merely the provider:
        # an anthropic call with no cacheable prefix (empty system, single turn)
        # places no marker and must not claim caching (G-8 honesty).
        pc_requested = pc
        pc_applied = pc_marker_placed
        pc_reason = None if pc_marker_placed else "no_cacheable_content"
    else:
        pc_requested, pc_applied, pc_reason = pc, False, "provider_inert"
    meta = LlmCallMeta(
        served_model=_served_model_of(completion, model),
        provider=provider,
        input_tokens=pt, output_tokens=ct, total_tokens=tt,
        started_at=started, ended_at=ended,
        response_format_fallback=fallback_reason,
        output_retries_used=retries_used,
        native_tool_calls=native_tool_calls,
        prompt_cache_requested=pc_requested,
        prompt_cache_applied=pc_applied,
        prompt_cache_reason=pc_reason,
        cache_read_tokens=cache_read,
        cache_creation_tokens=cache_creation,
    )
    return LlmResult(reply=reply, meta=meta)


def _resolve_acompletion(acompletion: Optional[AnyCompletion]) -> AnyCompletion:
    if acompletion is not None:
        return acompletion
    try:
        from any_llm import acompletion as any_llm_acompletion
    except ImportError as exc:  # pragma: no cover - exercised only without any-llm
        raise ImportError(
            "any-llm is required for the provider LLM caller; install "
            "julep[providers] plus your provider extra "
            "(e.g. pip install 'any-llm-sdk[anthropic,openai]')."
        ) from exc
    return any_llm_acompletion


def _resolve_aresponses(aresponses: Optional[AnyResponses]) -> AnyResponses:
    if aresponses is not None:
        return aresponses
    try:
        from any_llm import aresponses as any_llm_aresponses
    except ImportError as exc:  # pragma: no cover - exercised only without any-llm
        raise ImportError(
            "any-llm is required for the GPT-5.6 Responses caller; install "
            "julep[providers] plus the OpenAI provider extra "
            "(e.g. pip install 'any-llm-sdk[openai]')."
        ) from exc
    return any_llm_aresponses


# --------------------------------------------------------------------------- #
# Seam factories.
# --------------------------------------------------------------------------- #
def make_llm_caller(
    *,
    default_provider: str = DEFAULT_PROVIDER,
    acompletion: Optional[AnyCompletion] = None,
    aresponses: Optional[AnyResponses] = None,
) -> Callable[..., Awaitable[Any]]:
    """Activity-seam ``LlmCaller``: ``(Reasoner, value, principal, transcript, dispatch)``.

    The canonical 5-argument caller form: the principal is accepted (this
    caller resolves no per-tenant credentials itself) and the transcript is
    rendered into provider messages. Pass ``acompletion`` to inject a client
    (tests); otherwise any-llm's is imported lazily on first call.
    """

    async def caller(
        reasoner: Reasoner,
        value: Any,
        principal: Optional[dict[str, Any]] = None,
        transcript: Optional[list[dict[str, Any]]] = None,
        dispatch: ReasonerDispatch = _DEFAULT_REASONER_DISPATCH,
        *,
        tools: Optional[list[dict[str, Any]]] = None,
        parallel_tool_calls: Optional[bool] = None,
    ) -> Any:
        return await complete_reasoner(
            reasoner, value,
            acompletion=acompletion,
            aresponses=aresponses,
            default_provider=default_provider,
            transcript=transcript,
            dispatch=dispatch,
            tools=tools,
            parallel_tool_calls=parallel_tool_calls,
        )

    return caller


def make_local_reasoner(
    *,
    default_provider: str = DEFAULT_PROVIDER,
    acompletion: Optional[AnyCompletion] = None,
    aresponses: Optional[AnyResponses] = None,
) -> Callable[[str, Any], Awaitable[Any]]:
    """Facade-seam llm: ``(reasoner_name, payload) -> reply``.

    Resolves the registered :class:`Reasoner` by name (the facade passes the reasoner
    name) to recover ``model`` / ``system`` / ``reply_schema``.
    """

    async def caller(reasoner_name: str, payload: Any) -> Any:
        tools = None
        value = payload
        if isinstance(payload, dict) and NATIVE_TOOLS_KEY in payload:
            tools = payload[NATIVE_TOOLS_KEY]
            value = {key: val for key, val in payload.items() if key != NATIVE_TOOLS_KEY}
        return await complete_reasoner(
            get_reasoner(reasoner_name),
            value,
            acompletion=acompletion,
            aresponses=aresponses,
            default_provider=default_provider,
            tools=tools,
        )

    return caller


# --------------------------------------------------------------------------- #
# Resilient caller: deterministic fallback + circuit breaker around the core.
# --------------------------------------------------------------------------- #
def _with_model(reasoner: Reasoner, model: str) -> Reasoner:
    """A copy of ``reasoner`` addressed at a different model (not re-registered)."""
    if model == reasoner.model:
        return reasoner
    return Reasoner(
        name=reasoner.name,
        model=model,
        system=reasoner.system,
        tools=reasoner.tools,
        temperature=reasoner.temperature,
        max_rounds=reasoner.max_rounds,
        is_agent=reasoner.is_agent,
        sub_contract=reasoner.sub_contract,
        context_scope=reasoner.context_scope,
        system_render=reasoner.system_render,
        user_render=reasoner.user_render,
        max_tokens=reasoner.max_tokens,
        reply=reasoner.reply_schema,
        reasoning_effort=reasoner.reasoning_effort,
        output_retries=reasoner.output_retries,
        require_tool_call=reasoner.require_tool_call,
        response_format=reasoner.response_format,
        prompt_cache=reasoner.prompt_cache,
    )


def make_resilient_llm_caller(
    *,
    policy: ResiliencePolicy,
    breaker: Optional[CircuitBreaker] = None,
    on_attempt: Optional[OnAttempt] = None,
    classifier: Callable[[BaseException], ErrorClass] = classify_error,
    default_provider: str = DEFAULT_PROVIDER,
    acompletion: Optional[AnyCompletion] = None,
    aresponses: Optional[AnyResponses] = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> Callable[..., Awaitable[Any]]:
    """An ``LlmCaller`` that survives provider outages deterministically.

    Walks ``policy.candidates(reasoner.model)`` strictly in order. Per candidate:

    * an open circuit for the candidate's provider skips it (recorded, never
      silent);
    * TRANSIENT/TIMEOUT failures charge the breaker and retry the same model up
      to the policy's per-class budget (with backoff), then advance;
    * a CONFIG failure (bad key, unknown model, malformed request) re-raises
      immediately — a fallback must never mask misconfiguration;
    * when ``reasoner.reply_schema`` is set and the reply did not parse into a
      JSON object, that is MODEL_BEHAVIOR: advance to the next model without
      charging the breaker (the provider answered; the model misbehaved).

    Every attempt is reported through ``on_attempt`` (an
    :class:`~julep.resilience.AttemptRecord`) so workers can feed
    projection sinks / OTel with which model actually served. Providers whose
    SDKs wrap errors in custom hierarchies can swap ``classifier`` for their
    own ``exception -> ErrorClass`` mapping. When the chain is
    exhausted, raises :class:`~julep.errors.ResilienceExhausted`
    carrying the full attempt log.

    On Temporal, pair this with ``ExecutionPolicy(reasoner_max_attempts=1)`` so the
    engine's blind ``invokeReasoner`` retries do not multiply the ladder; on DBOS
    reasoner steps never retry, so this caller is the whole story by design.
    """

    def _notify(record: AttemptRecord) -> None:
        if on_attempt is not None:
            on_attempt(record)

    async def caller(
        reasoner: Reasoner,
        value: Any,
        principal: Optional[dict[str, Any]] = None,
        transcript: Optional[list[dict[str, Any]]] = None,
        dispatch: ReasonerDispatch = _DEFAULT_REASONER_DISPATCH,
        *,
        tools: Optional[list[dict[str, Any]]] = None,
        parallel_tool_calls: Optional[bool] = None,
    ) -> Any:
        attempts: list[AttemptRecord] = []
        last_exc: Optional[Exception] = None

        for model in policy.candidates(reasoner.model):
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

            candidate = _with_model(reasoner, model)
            attempt = 0
            while True:
                try:
                    result = await complete_reasoner(
                        candidate, value,
                        acompletion=acompletion,
                        aresponses=aresponses,
                        default_provider=default_provider,
                        transcript=transcript,
                        dispatch=dispatch,
                        tools=tools,
                        parallel_tool_calls=parallel_tool_calls,
                    )
                    reply = result.reply
                except ResponsesRefusalError as exc:
                    record = AttemptRecord(
                        model=model,
                        provider=provider,
                        outcome=ErrorClass.MODEL_BEHAVIOR.value,
                        detail=str(exc),
                    )
                    attempts.append(record)
                    _notify(record)
                    raise
                except ResponsesModelBehaviorError as exc:
                    record = AttemptRecord(
                        model=model,
                        provider=provider,
                        outcome=ErrorClass.MODEL_BEHAVIOR.value,
                        detail=str(exc),
                    )
                    attempts.append(record)
                    _notify(record)
                    last_exc = exc
                    break
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
                if reasoner.reply_schema is not None and not isinstance(reply, dict):
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
                replace_kwargs: dict[str, Any] = {
                    "attempts": tuple(
                        AttemptMeta(
                            model=a.model, provider=a.provider, outcome=a.outcome
                        )
                        for a in attempts
                    )
                }
                orig_provider, _ = _split_model(reasoner.model, default_provider)
                if (
                    reasoner.prompt_cache is not None
                    and orig_provider == "anthropic"
                    and provider != "anthropic"
                ):
                    replace_kwargs["prompt_cache_reason"] = "fallback_provider"
                meta = dataclasses.replace(result.meta, **replace_kwargs)
                return LlmResult(reply=reply, meta=meta)

        raise ResilienceExhausted(attempts) from last_exc

    return caller


__all__ = [
    "AnyCompletion",
    "AnyResponses",
    "DEFAULT_PROVIDER",
    "complete_reasoner",
    "make_llm_caller",
    "make_local_reasoner",
    "make_resilient_llm_caller",
    "provider_safe_tool_defs",
    "provider_safe_tool_name",
]
