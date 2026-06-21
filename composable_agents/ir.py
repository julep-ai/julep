"""The intermediate representation (blueprint §4).

A flow is a finite tree of :class:`Node`. The tree is the *only* thing the
harness, the analyzer, the validator and the projection ever agree on; the DSL
in :mod:`composable_agents.dsl` is sugar that emits this, and TypeScript emits
the same JSON. Recursion in the *evaluated* program only ever enters through
``iter_up_to`` / ``eval_plan`` / ``app`` — the tree of nodes stays finite, which
is what makes :func:`composable_agents.shapes.surface_shape` decidable.

Serialization uses camelCase keys (``summaryPolicy``, ``inputSchema``) so the
on-the-wire IR matches the blueprint's TS types verbatim. Canonical JSON (sorted
keys, no whitespace) is what we content-hash for replay checks.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterator, Optional, Union

from .kinds import ContextScope, Effect, Op, Shape, SummaryPolicy

JSONSchema = dict[str, Any]

# Reserved native tool: the harness turns a call to this into a human signal-wait
# rather than an HTTP request (see derived.human_gate / the interpreter).
HUMAN_GATE_TOOL = "__human_gate__"

# Reserved native tool: the harness turns a call to this into a durable timer
# (Temporal: workflow timer; DBOS: DBOS.sleep) rather than an HTTP request.
# The duration in seconds rides on the node's Ann.timeout.
SLEEP_TOOL = "__sleep__"


# --------------------------------------------------------------------------- #
# camelCase <-> snake_case helpers for the canonical JSON form.
# --------------------------------------------------------------------------- #
def _camel(name: str) -> str:
    head, *tail = name.split("_")
    return head + "".join(w.capitalize() for w in tail)


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


# --------------------------------------------------------------------------- #
# Tool references. A ToolRef is *unbound* in authored IR; freeze() binds each
# one to a content hash in the manifest.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class NativeTool:
    """An HTTP tool we own (Cloud Run / Lambda)."""

    name: str
    kind: str = "native"

    def to_json(self) -> dict[str, Any]:
        return {"kind": "native", "name": self.name}


@dataclass(frozen=True)
class McpTool:
    """A tool resolved from an MCP server and frozen at run start."""

    server: str
    tool: str
    kind: str = "mcp"

    def to_json(self) -> dict[str, Any]:
        return {"kind": "mcp", "server": self.server, "tool": self.tool}


ToolRef = Union[NativeTool, McpTool]


def toolref_from_json(d: dict[str, Any]) -> ToolRef:
    if d["kind"] == "native":
        return NativeTool(name=d["name"])
    if d["kind"] == "mcp":
        return McpTool(server=d["server"], tool=d["tool"])
    raise ValueError(f"unknown ToolRef kind: {d.get('kind')!r}")


def toolref_key(ref: ToolRef) -> str:
    """A stable, human-readable identifier used in manifests and capabilities."""
    if isinstance(ref, NativeTool):
        return ref.name
    return f"{ref.server}/{ref.tool}"


# --------------------------------------------------------------------------- #
# Context + caching + annotation leaves.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ContextPolicy:
    """Explicit declaration of how much session context a leaf reads.

    A ``WHOLE_SESSION`` branch inside a ``par`` is degraded to sequential by the
    validator, because two whole-session readers can't run concurrently without
    racing on the transcript.
    """

    scope: ContextScope = ContextScope.LOCAL
    redact_pii: bool = False
    max_tokens: Optional[int] = None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"scope": self.scope.value}
        if self.redact_pii:
            out["redactPii"] = True
        if self.max_tokens is not None:
            out["maxTokens"] = self.max_tokens
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "ContextPolicy":
        return ContextPolicy(
            scope=ContextScope(d.get("scope", "local")),
            redact_pii=bool(d.get("redactPii", False)),
            max_tokens=d.get("maxTokens"),
        )


@dataclass(frozen=True)
class CacheHint:
    key: Optional[str] = None
    ttl_s: Optional[int] = None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.key is not None:
            out["key"] = self.key
        if self.ttl_s is not None:
            out["ttlS"] = self.ttl_s
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "CacheHint":
        return CacheHint(key=d.get("key"), ttl_s=d.get("ttlS"))


@dataclass(init=False)
class Ann:
    """Optional per-node annotations: cost/risk hints, cache, timeout, retry."""

    cost: Optional[float] = None
    risk: Optional[str] = None
    cache: Optional[CacheHint] = None
    effect: Optional[Effect] = None
    timeout: Optional[int] = None  # seconds
    max_attempts: Optional[int] = None
    retry_interval_s: Optional[float] = None
    backoff_rate: Optional[float] = None
    batchable: bool = False

    def __init__(
        self,
        *,
        cost: Optional[float] = None,
        risk: Optional[str] = None,
        cache: Optional[CacheHint] = None,
        effect: Optional[Effect] = None,
        timeout_s: Optional[int] = None,
        max_attempts: Optional[int] = None,
        retry_interval_s: Optional[float] = None,
        backoff_rate: Optional[float] = None,
        batchable: bool = False,
    ) -> None:
        self.cost = cost
        self.risk = risk
        self.cache = cache
        self.effect = effect
        self.timeout = timeout_s
        self.max_attempts = max_attempts
        self.retry_interval_s = retry_interval_s
        self.backoff_rate = backoff_rate
        self.batchable = batchable

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.cost is not None:
            out["cost"] = self.cost
        if self.risk is not None:
            out["risk"] = self.risk
        if self.cache is not None:
            out["cache"] = self.cache.to_json()
        if self.effect is not None:
            out["effect"] = self.effect.value
        if self.timeout is not None:
            out["timeout"] = self.timeout
        if self.max_attempts is not None:
            out["maxAttempts"] = self.max_attempts
        if self.retry_interval_s is not None:
            out["retryIntervalS"] = self.retry_interval_s
        if self.backoff_rate is not None:
            out["backoffRate"] = self.backoff_rate
        if self.batchable:
            out["batchable"] = True
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "Ann":
        return Ann(
            cost=d.get("cost"),
            risk=d.get("risk"),
            cache=CacheHint.from_json(d["cache"]) if d.get("cache") else None,
            effect=Effect(d["effect"]) if d.get("effect") else None,
            timeout_s=d.get("timeout"),
            max_attempts=d.get("maxAttempts"),
            retry_interval_s=d.get("retryIntervalS"),
            backoff_rate=d.get("backoffRate"),
            batchable=bool(d.get("batchable", False)),
        )


# --------------------------------------------------------------------------- #
# Steps (prim payloads).
# --------------------------------------------------------------------------- #
@dataclass
class CallStep:
    tool: ToolRef
    ctx: Optional[ContextPolicy] = None
    # Bound by freeze() to the manifest content hash. None in authored IR.
    frozen_hash: Optional[str] = None
    kind: str = "call"

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"kind": "call", "tool": self.tool.to_json()}
        if self.ctx is not None:
            out["ctx"] = self.ctx.to_json()
        if self.frozen_hash is not None:
            out["frozenHash"] = self.frozen_hash
        return out


@dataclass
class ThinkStep:
    reasoner: str
    ctx: Optional[ContextPolicy] = None
    kind: str = "think"

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"kind": "think", "reasoner": self.reasoner}
        if self.ctx is not None:
            out["ctx"] = self.ctx.to_json()
        return out


@dataclass(frozen=True)
class SubContract:
    """The only thing that crosses the Joined firewall at the surface."""

    shape: Shape
    summary_policy: Optional[SummaryPolicy] = None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"shape": self.shape.value}
        if self.summary_policy is not None:
            out["summaryPolicy"] = self.summary_policy.value
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "SubContract":
        return SubContract(
            shape=Shape(d["shape"]),
            summary_policy=(
                SummaryPolicy(d["summaryPolicy"]) if d.get("summaryPolicy") else None
            ),
        )


@dataclass
class SubStep:
    ref: str
    contract: SubContract
    kind: str = "sub"

    def to_json(self) -> dict[str, Any]:
        return {"kind": "sub", "ref": self.ref, "contract": self.contract.to_json()}


Step = Union[CallStep, ThinkStep, SubStep]


def step_from_json(d: dict[str, Any]) -> Step:
    k = d["kind"]
    ctx = ContextPolicy.from_json(d["ctx"]) if d.get("ctx") else None
    if k == "call":
        return CallStep(
            tool=toolref_from_json(d["tool"]), ctx=ctx, frozen_hash=d.get("frozenHash")
        )
    if k == "think":
        return ThinkStep(reasoner=d["reasoner"], ctx=ctx)
    if k == "sub":
        return SubStep(ref=d["ref"], contract=SubContract.from_json(d["contract"]))
    raise ValueError(f"unknown Step kind: {k!r}")


def _budget_to_json(budget: Any) -> dict[str, Any]:
    if isinstance(budget, dict):
        out: dict[str, Any] = {}
        cost = budget.get("cost", budget.get("usd"))
        if cost is not None:
            out["cost"] = cost
        if "tokens" in budget and budget["tokens"] is not None:
            out["tokens"] = budget["tokens"]
        wall_seconds = budget.get("wallSeconds", budget.get("wall_seconds"))
        if wall_seconds is not None:
            out["wallSeconds"] = wall_seconds
        return out

    out = {}
    cost = getattr(budget, "cost", None)
    tokens = getattr(budget, "tokens", None)
    wall_seconds = getattr(budget, "wall_seconds", None)
    if cost is not None:
        out["cost"] = cost
    if tokens is not None:
        out["tokens"] = tokens
    if wall_seconds is not None:
        out["wallSeconds"] = wall_seconds
    return out


def _budget_from_json(d: dict[str, Any]) -> Any:
    from .capabilities import Budget

    return Budget(
        cost=d.get("cost", d.get("usd")),
        tokens=d.get("tokens"),
        wall_seconds=d.get("wallSeconds", d.get("wall_seconds")),
    )


# --------------------------------------------------------------------------- #
# Node.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Merge:
    """How a ``par`` node combines its branches.

    ``all`` waits for every branch (ordinary parallel/fanout). ``race`` and
    ``hedge`` take the first success and cancel the losers (a scheduling
    behavior the harness implements, not a post-hoc reduce). ``quorum`` waits for
    ``m`` successes. The kind is what §5 race admission keys off.
    """

    kind: str = "all"  # "all" | "race" | "hedge" | "quorum"
    hedge_ms: Optional[int] = None
    quorum_m: Optional[int] = None
    reducer: Optional[str] = None  # named pure applied to the collected results

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"kind": self.kind}
        if self.hedge_ms is not None:
            out["hedgeMs"] = self.hedge_ms
        if self.quorum_m is not None:
            out["quorumM"] = self.quorum_m
        if self.reducer is not None:
            out["reducer"] = self.reducer
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "Merge":
        return Merge(
            kind=d.get("kind", "all"),
            hedge_ms=d.get("hedgeMs"),
            quorum_m=d.get("quorumM"),
            reducer=d.get("reducer"),
        )


RACE_LIKE_MERGES = frozenset({"race", "hedge", "quorum"})


@dataclass
class Node:
    op: Op
    id: str
    ann: Optional[Ann] = None
    # prim:
    step: Optional[Step] = None
    # seq / par / alt:
    left: Optional["Node"] = None
    right: Optional["Node"] = None
    # alt switch:
    select: Optional[str] = None
    cases: Optional[dict[str, "Node"]] = None
    default: Optional["Node"] = None
    # iter_up_to (bound = max iterations) / each (bound = optional max_parallel,
    # pure = optional reducer over the collected per-item outputs):
    bound: Optional[int] = None
    body: Optional["Node"] = None
    # eval_plan:
    plan: Optional["Node"] = None
    # app:
    controller: Optional[str] = None
    # arr / alt predicate (named, content-addressed):
    pure: Optional[str] = None
    # arr static args: a named JSON object, serialized only when present.
    args: Optional[dict[str, Any]] = None
    # par join semantics (all/race/hedge/quorum). None == "all".
    merge: Optional[Merge] = None
    # DSL-only metadata held for later phases. APP inline config is serialized
    # below only when present; prompt stays out of the IR wire format.
    prompt: Optional[str] = None
    tools: Optional[Any] = None
    subflows: Optional[Any] = None
    budget: Optional[Any] = None
    max_rounds: Optional[int] = None
    # APP transcript carriage (docs/design/agent-transcripts.md): how much
    # session context the controller sees per round, and the named summarizer
    # reasoner for SUMMARY scope. Conditional keys: absent == today's LOCAL.
    ctx: Optional[ContextPolicy] = None
    summarizer: Optional[str] = None
    source: Optional["SourceSpan"] = None

    # ----- traversal -------------------------------------------------------- #
    def children(self) -> list["Node"]:
        kids = [self.left, self.right, self.body, self.plan]
        out = [k for k in kids if k is not None]
        if self.cases is not None:
            out.extend(self.cases[k] for k in sorted(self.cases))
        if self.default is not None:
            out.append(self.default)
        return out

    def walk(self) -> Iterator["Node"]:
        """Pre-order traversal over the node and all descendants."""
        yield self
        for k in self.children():
            yield from k.walk()

    def tool_refs(self) -> list[ToolRef]:
        refs: list[ToolRef] = []
        for n in self.walk():
            if n.step is not None and isinstance(n.step, CallStep):
                refs.append(n.step.tool)
        return refs

    # ----- serialization ---------------------------------------------------- #
    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"op": self.op.value, "id": self.id}
        if self.ann is not None:
            a = self.ann.to_json()
            if a:
                out["ann"] = a
        if self.step is not None:
            out["step"] = self.step.to_json()
        if self.left is not None:
            out["left"] = self.left.to_json()
        if self.right is not None:
            out["right"] = self.right.to_json()
        if self.select is not None:
            out["select"] = self.select
        if self.cases is not None:
            out["cases"] = {k: self.cases[k].to_json() for k in sorted(self.cases)}
        if self.default is not None:
            out["default"] = self.default.to_json()
        if self.bound is not None:
            out["bound"] = self.bound
        if self.body is not None:
            out["body"] = self.body.to_json()
        if self.plan is not None:
            out["plan"] = self.plan.to_json()
        if self.controller is not None:
            out["controller"] = self.controller
        if self.op == Op.APP:
            if self.tools is not None:
                out["tools"] = self.tools
            if self.subflows is not None:
                out["subflows"] = self.subflows
            if self.budget is not None:
                out["budget"] = _budget_to_json(self.budget)
            if self.max_rounds is not None:
                out["maxRounds"] = self.max_rounds
            if self.ctx is not None:
                out["ctx"] = self.ctx.to_json()
            if self.summarizer is not None:
                out["summarizer"] = self.summarizer
        if self.pure is not None:
            out["pure"] = self.pure
        if self.op == Op.ARR and self.args is not None:
            out["args"] = self.args
        if self.merge is not None:
            out["merge"] = self.merge.to_json()
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "Node":
        return Node(
            op=Op(d["op"]),
            id=d["id"],
            ann=Ann.from_json(d["ann"]) if d.get("ann") else None,
            step=step_from_json(d["step"]) if d.get("step") else None,
            left=Node.from_json(d["left"]) if d.get("left") else None,
            right=Node.from_json(d["right"]) if d.get("right") else None,
            select=d.get("select"),
            cases=(
                {str(k): Node.from_json(v) for k, v in d["cases"].items()}
                if "cases" in d
                else None
            ),
            default=Node.from_json(d["default"]) if d.get("default") else None,
            bound=d.get("bound"),
            body=Node.from_json(d["body"]) if d.get("body") else None,
            plan=Node.from_json(d["plan"]) if d.get("plan") else None,
            controller=d.get("controller"),
            pure=d.get("pure"),
            args=d.get("args"),
            merge=Merge.from_json(d["merge"]) if d.get("merge") else None,
            tools=d.get("tools"),
            subflows=d.get("subflows"),
            budget=_budget_from_json(d["budget"]) if "budget" in d else None,
            max_rounds=d.get("maxRounds", d.get("max_rounds")),
            ctx=ContextPolicy.from_json(d["ctx"]) if d.get("ctx") else None,
            summarizer=d.get("summarizer"),
        )


@dataclass(frozen=True)
class SourceSpan:
    file: str
    line: int
    function: Optional[str] = None
    text: Optional[str] = None


def canonical_json(value: Any) -> str:
    """Stable JSON used for content hashing: sorted keys, no whitespace."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def pure_display(name: str, args: Any = None) -> str:
    """Human-facing pure label including static args when present."""
    if args is None:
        return name
    try:
        encoded = canonical_json(args)
    except TypeError:
        encoded = repr(args)
    return f"{name} args={encoded}"
