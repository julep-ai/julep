"""OpenAI Responses API adapter for the GPT-5.6 model family.

Julep's provider-neutral LLM seam speaks the Chat Completions-shaped dialect
used by any-llm's ``acompletion`` API. GPT-5.6 tool-calling with reasoning must
use the Responses API instead, whose request and response shapes differ. This
module owns that translation so the agent loop, transcript model, and all
execution backends keep one neutral contract.

The adapter deliberately uses stateless requests (``store=False``) and
``reasoning.context=current_turn``. Julep already carries durable, neutral
agent state between controller rounds; provider-side conversation state would
make replay and continue-as-new depend on retained remote objects.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

AnyResponses = Callable[..., Awaitable[Any]]


class ResponsesStatusError(RuntimeError):
    """The Responses API returned a non-completed operational status."""


class ResponsesModelBehaviorError(RuntimeError):
    """The model returned an incomplete response."""


class ResponsesRefusalError(RuntimeError):
    """The model refused the request; callers must fail closed."""


def uses_openai_responses(provider: str, model: str) -> bool:
    """Whether this provider/model must use the Responses transport."""
    return provider == "openai" and (model == "gpt-5.6" or model.startswith("gpt-5.6-"))


def _responses_tool_defs(
    tools: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], set[str]]:
    """Return flattened definitions plus tools whose scalar input was wrapped."""
    out: list[dict[str, Any]] = []
    scalar_tools: set[str] = set()
    for tool in tools:
        if tool.get("type") != "function" or not isinstance(tool.get("function"), dict):
            raise ValueError("GPT-5.6 Responses transport only accepts function tools")
        function = dict(tool["function"])
        parameters = function.get("parameters")
        if isinstance(parameters, dict) and parameters.get("type") != "object":
            name = function.get("name")
            if isinstance(name, str):
                scalar_tools.add(name)
            function["parameters"] = {
                "type": "object",
                "properties": {"value": parameters},
                "required": ["value"],
                "additionalProperties": False,
            }
        # Chat Completions defaults to non-strict tools. Responses may otherwise
        # normalize a compatible schema into strict mode, so preserve Julep's
        # existing semantics explicitly when the author did not choose a mode.
        function.setdefault("strict", False)
        out.append({"type": "function", **function})
    return out, scalar_tools


def responses_tool_defs(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten Chat function tools and make every input schema an object."""
    return _responses_tool_defs(tools)[0]


def _unwrap_scalar_tool_arguments(result: Any, scalar_tools: set[str]) -> Any:
    """Restore Julep's bare-value convention after provider object wrapping."""
    if not scalar_tools:
        return result
    for item in getattr(result, "output", ()):
        if getattr(item, "type", None) != "function_call":
            continue
        if getattr(item, "name", None) not in scalar_tools:
            continue
        arguments = getattr(item, "arguments", "")
        try:
            parsed = json.loads(arguments)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if isinstance(parsed, dict) and set(parsed) == {"value"}:
            item.arguments = json.dumps(parsed["value"])
    return result


def responses_input(
    messages: list[dict[str, Any]],
    scalar_tools: set[str] | None = None,
    tool_name_aliases: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Translate Chat-style messages and tool history to Responses input items."""
    out: list[dict[str, Any]] = []
    scalar_tools = scalar_tools or set()
    tool_name_aliases = tool_name_aliases or {}
    for message in messages:
        role = message.get("role")
        tool_calls = message.get("tool_calls")
        if role == "assistant" and isinstance(tool_calls, list):
            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                tool_name = function.get("name")
                provider_tool_name = tool_name_aliases.get(tool_name, tool_name)
                arguments = function.get("arguments") or "{}"
                if provider_tool_name in scalar_tools:
                    try:
                        parsed_arguments = json.loads(arguments)
                    except (json.JSONDecodeError, TypeError, ValueError):
                        parsed_arguments = arguments
                    if not (
                        isinstance(parsed_arguments, dict)
                        and set(parsed_arguments) == {"value"}
                    ):
                        arguments = json.dumps({"value": parsed_arguments})
                out.append(
                    {
                        "type": "function_call",
                        "call_id": tool_call.get("id"),
                        "name": provider_tool_name,
                        "arguments": arguments,
                    }
                )
            continue
        if role == "tool" and message.get("tool_call_id"):
            content = message.get("content")
            out.append(
                {
                    "type": "function_call_output",
                    "call_id": message["tool_call_id"],
                    "output": content if isinstance(content, str) else json.dumps(content),
                }
            )
            continue
        if role in {"system", "developer", "user", "assistant"}:
            out.append({"role": role, "content": message.get("content") or ""})
            continue
        out.append({"role": "user", "content": json.dumps(message, sort_keys=True)})
    return out


def responses_format(response_format: dict[str, Any]) -> dict[str, Any]:
    """Translate Chat ``response_format`` to Responses ``text.format`` shape."""
    if response_format.get("type") != "json_schema":
        return response_format
    schema = response_format.get("json_schema", {})
    return {
        "type": "json_schema",
        "name": schema.get("name", "reply"),
        "schema": schema.get("schema", {}),
        "strict": bool(schema.get("strict", False)),
    }


async def call_openai_responses(
    aresponses: AnyResponses,
    *,
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    kwargs: dict[str, Any],
    tool_name_aliases: dict[str, str] | None = None,
) -> Any:
    """Map Julep/acompletion kwargs onto any-llm's ``aresponses`` call."""
    request: dict[str, Any] = {
        "provider": provider,
        "model": model,
        "store": False,
    }
    tools = kwargs.get("tools")
    scalar_tools: set[str] = set()
    if tools:
        request["tools"], scalar_tools = _responses_tool_defs(tools)
    request["input_data"] = responses_input(
        messages, scalar_tools, tool_name_aliases
    )
    if "parallel_tool_calls" in kwargs:
        request["parallel_tool_calls"] = kwargs["parallel_tool_calls"]
    effort = kwargs.get("reasoning_effort")
    reasoning: dict[str, Any] = {"context": "current_turn"}
    if effort is not None:
        reasoning["effort"] = effort
    request["reasoning"] = reasoning
    if "temperature" in kwargs:
        request["temperature"] = kwargs["temperature"]
    if "max_tokens" in kwargs:
        request["max_output_tokens"] = kwargs["max_tokens"]
    if "response_format" in kwargs:
        request["response_format"] = responses_format(kwargs["response_format"])
    if "service_tier" in kwargs:
        request["service_tier"] = kwargs["service_tier"]
    result = await aresponses(**request)
    return _unwrap_scalar_tool_arguments(result, scalar_tools)


def is_responses_result(result: Any) -> bool:
    """True for non-streaming Responses objects returned by any-llm."""
    return hasattr(result, "output") and not hasattr(result, "choices")


def parse_responses_reply(result: Any, *, expect_json: bool) -> tuple[Any, int]:
    """Extract Julep's neutral tool-call or text reply from Responses output."""
    status = getattr(result, "status", None)
    error = getattr(result, "error", None)
    incomplete = getattr(result, "incomplete_details", None)
    if error is not None or status in {"failed", "cancelled"}:
        raise ResponsesStatusError(
            f"Responses API returned status={status!r}, error={error!r}"
        )
    if status == "incomplete" or incomplete is not None:
        raise ResponsesModelBehaviorError(
            f"Responses API returned an incomplete response: {incomplete!r}"
        )
    if status not in {None, "completed"}:
        raise ResponsesStatusError(f"Responses API returned unexpected status={status!r}")
    tool_calls: list[dict[str, Any]] = []
    text_parts: list[str] = []
    for item in getattr(result, "output", ()):
        item_type = getattr(item, "type", None)
        if item_type == "function_call":
            arguments = getattr(item, "arguments", "")
            try:
                parsed_arguments = json.loads(arguments)
            except (json.JSONDecodeError, TypeError, ValueError):
                parsed_arguments = arguments
            tool_calls.append(
                {
                    "id": getattr(item, "call_id", None),
                    "tool": getattr(item, "name", None),
                    "input": parsed_arguments,
                }
            )
        elif item_type == "message":
            for part in getattr(item, "content", ()):
                if getattr(part, "type", None) == "output_text":
                    text = getattr(part, "text", None)
                    if isinstance(text, str):
                        text_parts.append(text)
                elif getattr(part, "type", None) == "refusal":
                    raise ResponsesRefusalError(
                        f"model refusal: {getattr(part, 'refusal', '')}"
                    )
    if tool_calls:
        return {"tool_calls": tool_calls}, len(tool_calls)
    text = "".join(text_parts)
    if not expect_json:
        return text, 0
    try:
        return json.loads(text.strip()), 0
    except (json.JSONDecodeError, TypeError, ValueError):
        return text, 0


def responses_usage(result: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(result, "usage", None)
    if usage is None:
        return None, None, None
    return (
        getattr(usage, "input_tokens", None),
        getattr(usage, "output_tokens", None),
        getattr(usage, "total_tokens", None),
    )


def responses_cache_usage(result: Any) -> tuple[int | None, int | None]:
    usage = getattr(result, "usage", None)
    details = getattr(usage, "input_tokens_details", None) if usage is not None else None
    return getattr(details, "cached_tokens", None), getattr(details, "cache_write_tokens", None)


__all__ = [
    "AnyResponses",
    "ResponsesModelBehaviorError",
    "ResponsesRefusalError",
    "ResponsesStatusError",
    "call_openai_responses",
    "is_responses_result",
    "parse_responses_reply",
    "responses_cache_usage",
    "responses_format",
    "responses_input",
    "responses_tool_defs",
    "responses_usage",
    "uses_openai_responses",
]
