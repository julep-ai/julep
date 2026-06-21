"""Framework-owned transcripts for ``app`` agent loops (design:
docs/design/agent-transcripts.md).

A transcript is *derived, not stored*: :func:`transcript_for` is a
deterministic projection of the agent loop's trace (plus the run input) into a
neutral, provider-agnostic list of :class:`Turn`. It emits the *plan* — turns
carry blob ``content_ref``s, not content. Hydration of refs, the token budget,
and summarization happen later, in the ``invoke_reasoner`` effect, where blob
refs can resolve outside workflow history.

Pure module: no IO, no engine imports, strict-typed. The budget helpers take
an injected ``TokenCounter`` (the worker supplies one via ``WorkerContext``;
:func:`approx_token_count` is the char-heuristic default — the real count is
the ``LlmCaller``'s business).
"""

from __future__ import annotations

import json
from typing import Any, Callable, Optional, Protocol, Sequence, TypedDict

from .ir import ContextPolicy
from .kinds import ContextScope


class _TurnRole(TypedDict):
    role: str  # "user" | "assistant" | "tool" | "system"


class Turn(_TurnRole, total=False):
    """One neutral transcript turn. ``ref`` names the action a turn describes
    (tool-ref JSON for calls, ``{"kind": "sub", "ref": ...}`` for sub-flows);
    a plan carries ``content_ref`` (a blob ref), a hydrated turn ``content``."""

    ref: dict[str, str]
    content: Any
    content_ref: str


Transcript = list[Turn]
TokenCounter = Callable[[str], int]

# The only ContextPolicy scopes that put a transcript on an app round; LOCAL
# (and NONE) keep today's {input, trace, last} behavior unchanged.
TRANSCRIPT_SCOPES = (ContextScope.WHOLE_SESSION, ContextScope.SUMMARY)

# Envelope key invokeReasoner uses to tool a freshly produced running summary back
# to the workflow (see split_summary_reply). Reserved; never a controller key.
SUMMARY_KEY = "__ca_summary__"


class TraceEntryView(Protocol):
    """Read-only view of one trace entry (structurally: agent_loop.TraceEntry)."""

    @property
    def decision(self) -> str: ...
    @property
    def ref(self) -> Optional[str]: ...
    @property
    def input_ref(self) -> Optional[str]: ...
    @property
    def output_ref(self) -> Optional[str]: ...


class AgentStateView(Protocol):
    """The minimal read-only slice of AgentState a transcript projects."""

    @property
    def trace(self) -> Sequence[TraceEntryView]: ...


def action_ref(decision: str, key: Optional[str]) -> dict[str, str]:
    """Neutral ref JSON for a trace entry's action (tool key or sub-flow ref)."""
    if decision == "sub":
        return {"kind": "sub", "ref": key or ""}
    if key and "/" in key:
        server, tool = key.split("/", 1)
        return {"kind": "mcp", "server": server, "tool": tool}
    return {"kind": "native", "name": key or ""}


def transcript_for(
    state: AgentStateView, policy: ContextPolicy, *, input: Any = None
) -> Transcript:
    """Project loop state into the ref-bearing transcript plan, oldest-first.

    Deterministic given the same state, policy, and run input — safe to compute
    in workflow code. Scopes outside :data:`TRANSCRIPT_SCOPES` yield ``[]``
    (today's behavior, unchanged). Each recorded action becomes an assistant
    turn (the decision) and a tool turn (its result); content stays behind
    ``content_ref`` blob refs until the effect hydrates them.
    """
    if policy.scope not in TRANSCRIPT_SCOPES:
        return []
    turns: Transcript = [{"role": "user", "content": input}]
    for entry in state.trace:
        if entry.decision not in ("call", "sub"):
            continue
        ref = action_ref(entry.decision, entry.ref)
        action: Turn = {"role": "assistant", "ref": ref}
        if entry.input_ref is not None:
            action["content_ref"] = entry.input_ref
        turns.append(action)
        result: Turn = {"role": "tool", "ref": ref}
        if entry.output_ref is not None:
            result["content_ref"] = entry.output_ref
        turns.append(result)
    return turns


# --------------------------------------------------------------------------- #
# Budget (hard bound) + elision / summary markers.
# --------------------------------------------------------------------------- #
def approx_token_count(text: str) -> int:
    """Char-heuristic default tokenizer (~4 chars per token)."""
    return (len(text) + 3) // 4


def turn_text(turn: Turn) -> str:
    """The deterministic text a token counter sees for one turn."""
    return json.dumps(turn, sort_keys=True, separators=(",", ":"))


def split_to_budget(
    turns: Sequence[Turn], max_tokens: int, count_tokens: TokenCounter
) -> tuple[list[Turn], list[Turn]]:
    """Split ``turns`` into ``(elided, kept)`` under a hard token bound.

    Keeps the *newest* turns whose cumulative count fits ``max_tokens``;
    everything older is elided. The bound is hard: if even the newest turn
    exceeds it, everything is elided (and the marker says so) — there is no
    silent overshoot.
    """
    kept_rev: list[Turn] = []
    total = 0
    ordered = list(turns)
    for turn in reversed(ordered):
        cost = count_tokens(turn_text(turn))
        if total + cost > max_tokens:
            break
        total += cost
        kept_rev.append(turn)
    kept = list(reversed(kept_rev))
    elided = ordered[: len(ordered) - len(kept)]
    return elided, kept


def elision_marker(count: int) -> Turn:
    """Explicit overflow marker: the model is told, never silently lied to."""
    return {"role": "system", "content": f"{count} earlier turns elided"}


def summary_turn(summary: str) -> Turn:
    """The running summary of elided turns, as a system turn (SUMMARY scope)."""
    return {"role": "system", "content": f"Summary of earlier turns:\n{summary}"}


def bounded_transcript(
    turns: Sequence[Turn], max_tokens: int, count_tokens: TokenCounter
) -> Transcript:
    """WHOLE_SESSION materialization: budget-bound turns, elision marker first."""
    elided, kept = split_to_budget(turns, max_tokens, count_tokens)
    if not elided:
        return kept
    return [elision_marker(len(elided)), *kept]


def split_summary_reply(reply: Any) -> tuple[Optional[str], Any]:
    """Unwrap the ``invokeReasoner`` summary envelope: ``(new_summary, reply)``.

    A SUMMARY-scope round whose summarizer ran returns
    ``{SUMMARY_KEY: <summary>, "reply": <controller reply>}`` so the workflow
    can persist the running summary in ``AgentState.summary`` without a second
    summarizer call. Everything else passes through as ``(None, reply)``.
    """
    if isinstance(reply, dict) and SUMMARY_KEY in reply:
        summary = reply[SUMMARY_KEY]
        return (str(summary) if summary is not None else None), reply.get("reply")
    return None, reply


__all__ = [
    "Turn",
    "Transcript",
    "TokenCounter",
    "TRANSCRIPT_SCOPES",
    "SUMMARY_KEY",
    "TraceEntryView",
    "AgentStateView",
    "action_ref",
    "transcript_for",
    "approx_token_count",
    "turn_text",
    "split_to_budget",
    "elision_marker",
    "summary_turn",
    "bounded_transcript",
    "split_summary_reply",
]
