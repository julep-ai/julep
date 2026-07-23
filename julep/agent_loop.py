"""The App agent loop and plan extraction (blueprint §P4), kept pure.

``Agent`` sits at the top of the shape lattice: an open-ended controller loop
that decides, round by round, what to do next. Two things keep that from being a
licence for unbounded, unsafe execution:

* **Bounded actions.** A controller does not emit arbitrary IR to run inline.
  Each round it returns one of a small, closed set of decisions
  (:func:`interpret_reasoner_reply`): *finish*, *escalate*, call one *granted tool*,
  or invoke one pre-registered *sub-flow*. Anything richer is the planner's job,
  not the agent's. This is what lets the loop run under Temporal without freezing
  and admitting fresh IR mid-flight.
* **A budget guard.** Every round charges an estimated cost; when the running
  total would exceed the capability budget (§9) the loop stops with
  ``over_budget`` instead of continuing. History growth is bounded separately by
  continue-as-new (:func:`should_continue_as_new`), the §6 seam the harness wires.

Plan *extraction* is the offline complement: an observed action trace is
macro-recorded into a candidate Plan (:func:`generalize_trace_to_plan`) which is
then run through §8 admission (:func:`extract_plan`) before it may be promoted to
a cheap, replayable :func:`~julep.dsl.stage`. This chains observed
calls; it does not infer branches, loops, reducers, or new procedures.

Everything here is dependency-free and deterministic so the loop's control logic
is unit-testable without a Temporal server; the durable wrapper that adds
activities and continue-as-new lives in :mod:`julep.execution.harness`.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Protocol

from .capabilities import Budget, CapabilityManifest
from .contracts import (
    CONSERVATIVE_DEFAULT,
    ToolContract,
    ToolManifest,
    contract_allows_retry,
)
from .dsl import Contract, call, ident, seq, sub
from .errors import PlanRejected
from .ir import ContextPolicy, Node, toolref_key
from .kinds import Effect, EnforcementMode, Idempotency, Shape
from .staged import admit_plan, estimate_cost, validate_plan
from .validate import Diagnostic


# Reserved controller-payload key carrying the per-round note (Task 7).
# Namespaced so an ordinary reasoner's business "note" field never renders
# as a system instruction (the prompt path opts in on THIS key only).
ROUND_NOTE_KEY = "__round_note__"
NATIVE_TOOLS_KEY = "__native_tools__"
# Reserved controller-payload key carrying loop feedback (require_tool_call
# re-asks, output-validation re-asks) on transcript-scoped rounds, where the
# conversation itself lives in the transcript and transcript_for deliberately
# excludes reask trace entries. The prompt path renders it as a trailing user
# turn instead of re-rendering the business template against the feedback.
FEEDBACK_KEY = "__loop_feedback__"
REQUIRE_TOOL_CALL_REASK_MESSAGE = "require_tool_call: reply with a tool call, not text"
REQUIRE_TOOL_CALL_NEVER_CALLED_REASON = (
    "require_tool_call: controller never called a tool"
)


def coerce_round_note(note: Any) -> Optional[str]:
    """Enforce the round_note pure's ``(ctx) -> Optional[str]`` contract.

    None means "no note this round"; a str is the note. Any other type is a
    loud teaching error (G-8: no silent fallbacks) rather than a value that
    would be silently dropped by the prompt renderer.
    """
    if note is None or isinstance(note, str):
        return note
    raise ValueError(
        f"round_note pure must return str | None, got {type(note).__name__}: {note!r}"
    )


# --------------------------------------------------------------------------- #
# Round decisions.
# --------------------------------------------------------------------------- #
class Decision(str, Enum):
    """What a controller asked the loop to do this round."""

    FINISH = "finish"      # done: payload is the final output
    ESCALATE = "escalate"  # give up to a human/parent: payload is a reason
    CALL = "call"          # invoke a granted tool: payload is {"tool", "input"}
    CALL_MANY = "call_many"  # invoke granted tools: payload is [{"id", "tool", "input"}, ...]
    SUB = "sub"            # invoke a registered sub-flow: payload is {"ref", "input", "shape"?}
    CONTROLLER_ERROR = "controller_error"  # malformed controller output


# Default per-action cost estimate (cost units), used when the controller does not
# report an actual cost. Deliberately conservative so the budget guard trips
# early rather than late. Matches the structural defaults in ``staged``.
DEFAULT_TOOL_COST = 1.0
DEFAULT_SUB_COST = 5.0
DEFAULT_THINK_COST = 2.0  # the controller's own per-round model call


@dataclass(frozen=True)
class RoundAction:
    """A normalized, validated controller decision for one round."""

    decision: Decision
    payload: Any = None

    @property
    def is_terminal(self) -> bool:
        return self.decision in (Decision.FINISH, Decision.ESCALATE, Decision.CONTROLLER_ERROR)


class ToolCaller(Protocol):
    def __call__(
        self,
        name: str,
        value: Any,
        *,
        call_index: Optional[int] = None,
    ) -> Awaitable[Any]:
        ...


def interpret_reasoner_reply(
    reply: Any, *, strict: bool = True, native_tools: bool = False
) -> RoundAction:
    """Map a controller's structured reply to a :class:`RoundAction`.

    Accepts the small, closed action vocabulary the loop supports. In strict
    mode, malformed output is a controller error. Set ``strict=False`` to retain
    the legacy behavior where prose or unknown shapes finish with the raw reply.
    """
    def malformed() -> RoundAction:
        if strict:
            return RoundAction(
                Decision.CONTROLLER_ERROR,
                f"malformed controller reply: {reply!r}",
            )
        return RoundAction(Decision.FINISH, reply)

    if not isinstance(reply, dict):
        return malformed()

    if native_tools and "tool_calls" in reply:
        entries = reply["tool_calls"]
        if not isinstance(entries, list) or not entries:
            return malformed()
        calls: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("tool"), str):
                return malformed()
            calls.append(
                {
                    "id": entry.get("id"),
                    "tool": entry["tool"],
                    "input": entry.get("input"),
                }
            )
        return RoundAction(Decision.CALL_MANY, calls)

    # Finish: explicit done flag, or a bare {"output": ...}.
    if reply.get("done") is True or ("output" in reply and "tool" not in reply and "sub" not in reply):
        return RoundAction(Decision.FINISH, reply.get("output", reply))

    if "escalate" in reply:
        return RoundAction(Decision.ESCALATE, reply.get("escalate") or "escalated by controller")

    if "tool" in reply:
        payload = {
            "tool": reply["tool"],
            "input": reply.get("input", reply.get("args")),
        }
        if reply.get("id") is not None:
            payload["id"] = reply["id"]
        return RoundAction(
            Decision.CALL,
            payload,
        )

    if "sub" in reply:
        return RoundAction(
            Decision.SUB,
            {
                "ref": reply["sub"],
                "input": reply.get("input"),
                "shape": reply.get("shape", Shape.PIPELINE.value),
            },
        )

    return malformed()


def action_cost(action: RoundAction, reported: Optional[float] = None) -> float:
    """Cost to charge for an action this round (controller-reported or default)."""
    if reported is not None:
        return float(reported)
    if action.decision is Decision.CALL:
        return DEFAULT_TOOL_COST
    if action.decision is Decision.CALL_MANY:
        return DEFAULT_TOOL_COST * len(action.payload)
    if action.decision is Decision.SUB:
        return DEFAULT_SUB_COST
    return 0.0


@dataclass(frozen=True)
class CallDenial:
    """A settled policy refusal for an agent CALL decision."""

    reason: str


# --------------------------------------------------------------------------- #
# Loop config + state (continue-as-new safe: fully JSON round-trippable).
# --------------------------------------------------------------------------- #
@dataclass
class AgentConfig:
    """Static policy for an agent run."""

    max_rounds: int = 24
    budget: Optional[Budget] = None
    mode: EnforcementMode = EnforcementMode.STRICT
    # §6 seam: after this many rounds, the durable harness calls continue_as_new
    # to truncate Temporal history. 0 disables (history grows unbounded — fine
    # for short agents, a footgun for long ones).
    continue_as_new_after: int = 0
    # Per-round controller call cost, charged in addition to the action.
    think_cost: float = DEFAULT_THINK_COST
    # Spec §10: malformed controller output is an error unless explicitly opted out.
    permissive_controller: bool = False
    # Transcript carriage (docs/design/agent-transcripts.md): context policy for
    # the controller's rounds, and the named summarizer reasoner for SUMMARY scope.
    ctx: Optional[ContextPolicy] = None
    summarizer: Optional[str] = None
    native_tools: bool = False
    require_tool_call: bool = False
    round_note: Optional[str] = None
    output_schema: Optional[dict[str, Any]] = None
    output_retries: int = 0

    @staticmethod
    def from_json(d: dict[str, Any]) -> "AgentConfig":
        return AgentConfig(
            max_rounds=int(d.get("maxRounds", d.get("max_rounds", 24))),
            budget=Budget.from_dict(d.get("budget")),
            mode=EnforcementMode.coerce(d.get("mode", EnforcementMode.STRICT)),
            continue_as_new_after=int(
                d.get("continueAsNewAfter", d.get("continue_as_new_after", 0))
            ),
            think_cost=float(d.get("thinkCost", d.get("think_cost", DEFAULT_THINK_COST))),
            permissive_controller=bool(
                d.get("permissiveController", d.get("permissive_controller", False))
            ),
            ctx=ContextPolicy.from_json(d["ctx"]) if d.get("ctx") else None,
            summarizer=d.get("summarizer"),
            native_tools=bool(d.get("nativeTools", d.get("native_tools", False))),
            require_tool_call=bool(
                d.get("requireToolCall", d.get("require_tool_call", False))
            ),
            round_note=d.get("roundNote", d.get("round_note")),
            output_schema=d.get("replySchema", d.get("reply_schema")),
            output_retries=int(d.get("outputRetries", d.get("output_retries", 0))),
        )

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "maxRounds": self.max_rounds,
            "mode": EnforcementMode.coerce(self.mode).value,
            "continueAsNewAfter": self.continue_as_new_after,
            "thinkCost": self.think_cost,
            "permissiveController": self.permissive_controller,
        }
        if self.budget is not None:
            b: dict[str, Any] = {}
            if self.budget.cost is not None:
                b["cost"] = self.budget.cost
            if self.budget.tokens is not None:
                b["tokens"] = self.budget.tokens
            if self.budget.wall_seconds is not None:
                b["wallSeconds"] = self.budget.wall_seconds
            out["budget"] = b
        if self.ctx is not None:
            out["ctx"] = self.ctx.to_json()
        if self.summarizer is not None:
            out["summarizer"] = self.summarizer
        if self.native_tools:
            out["nativeTools"] = True
        if self.require_tool_call:
            out["requireToolCall"] = True
        if self.round_note is not None:
            out["roundNote"] = self.round_note
        if self.output_schema is not None:
            out["replySchema"] = self.output_schema
        if self.output_retries:
            out["outputRetries"] = self.output_retries
        return out

    @staticmethod
    def from_capabilities(caps: Optional[CapabilityManifest], **overrides: Any) -> "AgentConfig":
        cfg = AgentConfig(budget=caps.budget if caps else None)
        for k, v in overrides.items():
            setattr(cfg, k, v)
        return cfg


def tool_input_schemas(
    tool_defs: Optional[Sequence[Mapping[str, Any]]],
) -> dict[str, dict[str, Any]]:
    """Extract the frozen provider-name -> input-schema map.

    Tool definitions cross release/workflow boundaries as JSON, so validate the
    small provider shape once before model rounds begin instead of silently
    dispatching an unvalidated call when metadata is malformed.
    """
    schemas: dict[str, dict[str, Any]] = {}
    for index, definition in enumerate(tool_defs or ()):
        function = definition.get("function")
        if not isinstance(function, Mapping):
            raise ValueError(f"toolDefs[{index}].function must be an object")
        name = function.get("name")
        parameters = function.get("parameters")
        if not isinstance(name, str) or not name:
            raise ValueError(f"toolDefs[{index}].function.name must be a non-empty string")
        if not isinstance(parameters, dict):
            raise ValueError(f"toolDefs[{index}].function.parameters must be an object")
        if name in schemas:
            raise ValueError(f"toolDefs defines {name!r} more than once")
        schemas[name] = parameters
    return schemas


@dataclass
class TraceEntry:
    """One recorded action and its result (the raw material for plan extraction)."""

    decision: str
    ref: Optional[str] = None      # tool name or sub-flow ref
    shape: Optional[str] = None    # sub-flow surface shape, if a sub
    cost: float = 0.0
    input_ref: Optional[str] = None
    output_ref: Optional[str] = None
    schema_ref: Optional[str] = None
    call_id: Optional[str] = None
    # Canonical call arguments live in durable loop state independently of
    # provider prompt truncation. ``input_ref`` remains the optional blob ref.
    arguments: Any = None
    error: Optional[str] = None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"decision": self.decision, "cost": self.cost}
        if self.ref is not None:
            out["ref"] = self.ref
        if self.shape is not None:
            out["shape"] = self.shape
        if self.input_ref is not None:
            out["inputRef"] = self.input_ref
        if self.output_ref is not None:
            out["outputRef"] = self.output_ref
        if self.schema_ref is not None:
            out["schemaRef"] = self.schema_ref
        if self.call_id is not None:
            out["callId"] = self.call_id
        if self.arguments is not None:
            out["arguments"] = self.arguments
        if self.error is not None:
            out["error"] = self.error
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "TraceEntry":
        return TraceEntry(
            decision=d["decision"], ref=d.get("ref"),
            shape=d.get("shape"), cost=float(d.get("cost", 0.0)),
            input_ref=d.get("inputRef", d.get("input_ref")),
            output_ref=d.get("outputRef", d.get("output_ref")),
            schema_ref=d.get("schemaRef", d.get("schema_ref")),
            call_id=d.get("callId", d.get("call_id")),
            arguments=d.get("arguments"),
            error=d.get("error"),
        )


STATE_SCHEMA_VERSION = 1


@dataclass
class AgentState:
    """Mutable loop state. Round-trips through JSON for continue-as-new."""

    round: int = 0
    spent: float = 0.0
    last: Any = None
    trace: list[TraceEntry] = field(default_factory=list)
    call_counts: dict[str, int] = field(default_factory=dict)
    controller_meta: Optional[dict[str, Any]] = None
    # Running summary of elided transcript turns (SUMMARY scope only); persists
    # across continue_as_new so a new segment never re-summarizes from blobs.
    summary: Optional[str] = None

    def charge(self, cost: float) -> None:
        self.spent += cost

    def record(self, entry: TraceEntry) -> None:
        self.trace.append(entry)

    def to_json(self) -> dict[str, Any]:
        out = {
            "schemaVersion": STATE_SCHEMA_VERSION,
            "round": self.round,
            "cost": self.spent,
            "last": self.last,
            "trace": [t.to_json() for t in self.trace],
        }
        if self.call_counts:
            out["callCounts"] = dict(sorted(self.call_counts.items()))
        if self.summary is not None:
            out["summary"] = self.summary
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "AgentState":
        version = int(d.get("schemaVersion", STATE_SCHEMA_VERSION))
        if version > STATE_SCHEMA_VERSION:
            raise ValueError(
                f"AgentState schemaVersion {version} is newer than supported "
                f"{STATE_SCHEMA_VERSION}; add a migration in agent_loop.AgentState.from_json"
            )
        return AgentState(
            round=int(d.get("round", 0)),
            spent=float(d.get("cost", d.get("spentUsd", 0.0))),
            last=d.get("last"),
            trace=[TraceEntry.from_json(t) for t in d.get("trace", [])],
            call_counts={
                str(tool): int(count)
                for tool, count in d.get("callCounts", d.get("call_counts", {})).items()
            },
            summary=d.get("summary"),
        )


async def blob_round_output_refs(
    state: AgentState,
    prev_trace_len: int,
    blob: Callable[[Any], Awaitable[str]],
) -> None:
    """Assign per-entry output_ref blobs to call/sub trace entries recorded this round.

    A CALL_MANY round records several call entries and leaves ``state.last`` as the
    aligned observation list. Each entry gets its own output blob. Single call/sub
    rounds record one entry and keep the existing ``state.last`` semantics.
    """
    new_entries = [
        entry
        for entry in state.trace[prev_trace_len:]
        if entry.decision in (Decision.CALL.value, Decision.SUB.value)
    ]
    if not new_entries:
        return
    if len(new_entries) == 1:
        new_entries[0].output_ref = await blob(state.last)
        return

    observations = (
        state.last if isinstance(state.last, list) else [state.last] * len(new_entries)
    )
    for entry, obs in zip(new_entries, observations, strict=False):
        value = obs["output"] if isinstance(obs, dict) and "output" in obs else obs
        entry.output_ref = await blob(value)


def state_fingerprint(state: AgentState) -> str:
    """Stable sha256 hex of the canonical JSON of ``state.to_json()``.

    The commit-idempotency key the SessionStore keys on (design invariant 2):
    order-independent (equal states up to dict ordering hash identically) and
    sensitive to any field change. The session-store path requires the whole
    ``AgentState`` (including ``last`` and trace entries) to be
    JSON-serializable — the same constraint the SessionStore's persistence of
    ``state.to_json()`` already imposes.
    """
    try:
        canonical = json.dumps(state.to_json(), sort_keys=True, separators=(",", ":"))
    except TypeError as exc:
        raise TypeError(
            "state_fingerprint: AgentState is not JSON-serializable "
            f"({exc}). The session-store path requires AgentState — including "
            "`last` and trace entries — to be JSON-serializable, because the "
            "SessionStore persists state.to_json() as canonical JSON. The "
            "default inline continue-as-new path has no such restriction."
        ) from exc
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Budget + continue-as-new policy (pure predicates the harness consults).
# --------------------------------------------------------------------------- #
def would_exceed_budget(state: AgentState, next_cost: float, budget: Optional[Budget]) -> bool:
    """True if charging ``next_cost`` would push the run over its cost budget."""
    if budget is None or budget.cost is None:
        return False
    return state.spent + next_cost > budget.cost


def should_continue_as_new(state: AgentState, cfg: AgentConfig, *, baseline_round: int = 0) -> bool:
    """True when the durable harness should truncate history via continue-as-new.

    ``baseline_round`` is the cumulative round count at segment entry. Carried
    state keeps the cumulative ``state.round`` across truncations, so the
    cadence is measured per segment: fire once the current segment has run
    ``cfg.continue_as_new_after`` rounds past its baseline.
    """
    return (
        cfg.continue_as_new_after > 0
        and (state.round - baseline_round) >= cfg.continue_as_new_after
    )


def terminal_result(status: str, state: AgentState, output: Any = None,
                    reason: Optional[str] = None) -> dict[str, Any]:
    """Uniform shape for everything the agent loop can return."""
    out: dict[str, Any] = {
        "status": status,
        "output": output if output is not None else state.last,
        "rounds": state.round,
        "cost": state.spent,
        "trace": [t.to_json() for t in state.trace],
    }
    if reason is not None:
        out["reason"] = reason
    if state.call_counts:
        out["callCounts"] = dict(sorted(state.call_counts.items()))
    if state.controller_meta:
        out["__julep_meta__"] = dict(state.controller_meta)
    return out


AgentContractMap = dict[str, dict[str, Any]]


def precheck_controller(state: AgentState, cfg: AgentConfig) -> Optional[dict[str, Any]]:
    """Terminate before a controller call when the think cost would exceed budget."""
    if would_exceed_budget(state, cfg.think_cost, cfg.budget):
        return terminal_result("over_budget", state)
    return None


def _approval_bool(raw: Any) -> bool:
    if isinstance(raw, str):
        return raw.lower() in {"1", "true", "yes", "required"}
    return bool(raw)


def contract_for_tool(tool: str, contracts: Optional[AgentContractMap]) -> ToolContract:
    """Return the carried contract for ``tool``, defaulting conservatively."""
    raw = (contracts or {}).get(tool)
    if raw is None:
        return CONSERVATIVE_DEFAULT
    return ToolContract(
        effect=Effect(raw.get("effect", CONSERVATIVE_DEFAULT.effect.value)),
        idempotency=Idempotency(raw.get("idempotency", CONSERVATIVE_DEFAULT.idempotency.value)),
    )


def contract_asserted_for_tool(tool: str, contracts: Optional[AgentContractMap]) -> bool:
    """Whether the carried contract has trusted retry authority.

    Missing fields are legacy/unasserted and therefore fail closed.  An MCP
    hint can describe a read or idempotent operation, but it cannot grant the
    framework permission to repeat a call.
    """

    raw = (contracts or {}).get(tool) or {}
    return raw.get("asserted") is True


def approval_required_for_tool(tool: str, contracts: Optional[AgentContractMap]) -> bool:
    """True when a carried contract/grant requires human approval."""
    raw = (contracts or {}).get(tool) or {}
    contract = contract_for_tool(tool, contracts)
    return contract.effect == Effect.DANGEROUS or _approval_bool(raw.get("approval", False))


def authorize_call(
    tool: str,
    *,
    unconstrained: bool,
    granted_set: set[str],
    contracts: Optional[AgentContractMap],
) -> Optional[CallDenial]:
    """Authorize one agent CALL against grants and approval-only contracts."""
    if not unconstrained and tool not in granted_set:
        return CallDenial(reason=f"tool {tool!r} is not granted")
    if approval_required_for_tool(tool, contracts):
        return CallDenial(reason=f"approval-required tool {tool!r}; agent must ESCALATE")
    return None


def max_calls_for_tool(tool: str, contracts: Optional[AgentContractMap]) -> Optional[int]:
    """Return the carried maxCalls limit for ``tool``, if any."""
    raw = (contracts or {}).get(tool) or {}
    limit = raw.get("maxCalls", raw.get("max_calls"))
    return int(limit) if limit is not None else None


def charge_tool_call(
    state: AgentState,
    tool: str,
    contracts: Optional[AgentContractMap],
    *,
    count_key: Optional[str] = None,
) -> Optional[CallDenial]:
    """Increment one deterministic tool budget counter, or return a denial.

    ``tool`` is the provider-visible name used for contracts and diagnostics.
    ``count_key`` is its canonical capability identity when multiple provider
    aliases dispatch to the same wire tool.
    """
    limit = max_calls_for_tool(tool, contracts)
    if limit is None:
        return None
    key = tool if count_key is None else count_key
    count = state.call_counts.get(key, 0)
    if count >= limit:
        return CallDenial(reason=f"tool {tool!r} exceeded maxCalls={limit}")
    state.call_counts[key] = count + 1
    return None


def authorize_subflow(
    ref: str,
    *,
    granted_subflows: Optional[set[str]],
) -> Optional[CallDenial]:
    """Authorize one agent SUB decision against None/allow-list grants."""
    if granted_subflows is not None and ref not in granted_subflows:
        return CallDenial(reason=f"subflow {ref!r} is not granted")
    return None


def retry_max_attempts_for_contract(
    contract: ToolContract,
    *,
    asserted: bool = False,
    idempotent_max_attempts: int,
    write_max_attempts: int,
) -> int:
    """Choose retry attempts from a pure tool contract.

    Idempotency gates whether a call may retry at all. ``write_max_attempts`` is
    retained for policy JSON compatibility, but non-idempotent writes collapse
    to one attempt.
    """
    if asserted and contract_allows_retry(contract):
        return idempotent_max_attempts
    return 1


def manifest_contracts_for_agent(
    manifest: ToolManifest,
    granted_tools: Optional[Sequence[str]],
    max_call_limits: Optional[dict[str, int]] = None,
) -> dict[str, dict[str, Any]]:
    """Serialize frozen contracts by tool key for the child agent workflow."""
    wanted = None if granted_tools is None else set(granted_tools)
    contracts: dict[str, dict[str, Any]] = {}
    for frozen in manifest.values():
        key = toolref_key(frozen.ref)
        if wanted is None or key in wanted:
            payload = frozen.contract.to_json()
            payload["asserted"] = frozen.asserted
            if frozen.assertion_provenance is not None:
                payload["assertionProvenance"] = frozen.assertion_provenance
            if max_call_limits is not None and key in max_call_limits:
                payload["maxCalls"] = int(max_call_limits[key])
            contracts[key] = payload
    return contracts


def max_call_limits_from_contracts(
    contracts: Optional[dict[str, dict[str, Any]]],
    tool_aliases: Optional[Mapping[str, str]] = None,
) -> Optional[dict[str, int]]:
    """Extract limits, optionally canonicalized to wire-tool identities."""
    limits: dict[str, int] = {}
    for tool, raw in (contracts or {}).items():
        limit = raw.get("maxCalls", raw.get("max_calls"))
        if limit is not None:
            key = (tool_aliases or {}).get(tool, tool)
            value = int(limit)
            limits[key] = min(limits.get(key, value), value)
    return limits or None


async def drive_agent_loop(
    *,
    input: Any,
    cfg: AgentConfig,
    invoke_controller: Callable[[dict[str, Any]], Awaitable[Any]],
    call_tool: ToolCaller,
    run_subflow: Optional[Callable[[str, Any], Awaitable[Any]]] = None,
    granted: Optional[set[str]] = None,
    granted_subflows: Optional[set[str]] = None,
    contracts: Optional[AgentContractMap] = None,
    tool_count_keys: Optional[Mapping[str, str]] = None,
    tool_schemas: Optional[Mapping[str, dict[str, Any]]] = None,
    state: Optional[AgentState] = None,
    get_pure: Optional[Callable[[str], Callable[..., Any]]] = None,
) -> dict[str, Any]:
    """Run the bounded agent loop locally with injected async effects."""
    from .turn import controller_turn, drive, make_finalize, pre_round

    mode = EnforcementMode.coerce(cfg.mode)
    prod_gap: list[str] = []
    state = state or AgentState(last=input)
    step = controller_turn(
        cfg=cfg, invoke_controller=invoke_controller, call_tool=call_tool,
        run_subflow=run_subflow, granted=granted, granted_subflows=granted_subflows,
        contracts=contracts, tool_count_keys=tool_count_keys, mode=mode,
        prod_gap=prod_gap, run_input=input,
        get_pure=get_pure, tool_schemas=tool_schemas,
    )
    return await drive(step, state, halt=pre_round(cfg), finalize=make_finalize(prod_gap))


# --------------------------------------------------------------------------- #
# Plan extraction (offline generalization of an observed trace).
# --------------------------------------------------------------------------- #
def generalize_trace_to_plan(trace: list[TraceEntry]) -> Node:
    """Macro-record a successful action trace into straight-line candidate IR.

    Calls become :func:`~julep.dsl.call` leaves and sub-flow
    invocations become :func:`~julep.dsl.sub` leaves, chained in
    observed order with :func:`~julep.dsl.seq`. Terminal
    decisions (finish/escalate) carry no tool and are skipped. This is a
    macro-recording of observed calls; it does not infer branches, loops,
    reducers, or latent procedure structure. The result is a *candidate* only —
    it must clear :func:`extract_plan` before promotion.

    The generalization is deliberately shallow (a pipeline, never a loop or a
    stage), which keeps every extracted plan within the ``<= Feedback`` ceiling
    that §8 admission enforces.
    """
    leaves: list[Node] = []
    for t in trace:
        if t.decision == Decision.CALL.value and t.ref:
            leaves.append(call(t.ref))
        elif t.decision == Decision.SUB.value and t.ref:
            shape = Shape(t.shape) if t.shape else Shape.PIPELINE
            leaves.append(sub(t.ref, Contract.of(shape)))
    if not leaves:
        return ident()
    if len(leaves) == 1:
        return leaves[0]
    return seq(*leaves)


def extract_plan(
    trace: list[TraceEntry],
    parent: CapabilityManifest,
    manifest: Optional[ToolManifest] = None,
) -> tuple[Node, list[Diagnostic]]:
    """Macro-record ``trace`` to a plan and return it with §8 diagnostics.

    Does not raise: a caller inspecting whether an observed agent run is safe to
    promote wants the diagnostics, not an exception. Use :func:`promote_plan`
    when you want admission to be enforced. This path chains observed actions;
    it does not discover branches, loops, reducers, or new procedures.
    """
    plan = generalize_trace_to_plan(trace)
    diags = validate_plan(plan, parent, manifest)
    return plan, diags


def promote_plan(
    trace: list[TraceEntry],
    parent: CapabilityManifest,
    manifest: Optional[ToolManifest] = None,
) -> Node:
    """Macro-record and admit an observed trace, returning the promotable plan.

    Raises :class:`~julep.errors.PlanRejected` if the generalized
    plan would not pass §8 admission (e.g. it references an ungranted tool or
    exceeds the budget), mirroring runtime plan staging exactly.
    """
    plan = generalize_trace_to_plan(trace)
    return admit_plan(plan, parent, manifest)  # raises PlanRejected on any blocking diag


__all__ = [
    "Decision",
    "RoundAction",
    "interpret_reasoner_reply",
    "action_cost",
    "AgentConfig",
    "tool_input_schemas",
    "AgentState",
    "STATE_SCHEMA_VERSION",
    "TraceEntry",
    "would_exceed_budget",
    "should_continue_as_new",
    "blob_round_output_refs",
    "state_fingerprint",
    "terminal_result",
    "CallDenial",
    "coerce_round_note",
    "precheck_controller",
    "contract_for_tool",
    "contract_asserted_for_tool",
    "approval_required_for_tool",
    "authorize_call",
    "max_calls_for_tool",
    "charge_tool_call",
    "authorize_subflow",
    "retry_max_attempts_for_contract",
    "manifest_contracts_for_agent",
    "max_call_limits_from_contracts",
    "drive_agent_loop",
    "generalize_trace_to_plan",
    "extract_plan",
    "promote_plan",
    "estimate_cost",
    "PlanRejected",
    "REQUIRE_TOOL_CALL_REASK_MESSAGE",
    "REQUIRE_TOOL_CALL_NEVER_CALLED_REASON",
]
