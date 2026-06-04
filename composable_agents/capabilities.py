"""The capability manifest (blueprint §9).

A capability manifest is the human-authored contract that says what a deployed
flow is *allowed* to touch: which tools (and with what asserted effect /
idempotency), which brains, which memory scopes, which MCP servers (at which
versions), and the overall budget. It does two jobs:

1. It is the only sanctioned source of *asserted* tool contracts. ``freeze``
   trusts an MCP tool's contract only when it appears here (see
   :func:`CapabilityManifest.overrides`); otherwise the contract is defaulted
   conservatively from untrusted hints and the tool can't race (§5).
2. It is an allow-list enforced at three seams (§9): *compile* (every referenced
   tool / brain / server / memory scope must be granted — :func:`enforce_compile`),
   *schedule* (budget, surfaced to the agent guard and the plan estimator), and
   *run* (network egress + model allow-list, checked inside the activity).

Allow-list semantics are explicit: an **absent** section means "unconstrained";
a **present** section is a deny-by-default allow-list. So omitting ``brains``
permits any brain, but listing two brains forbids a third.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .errors import CapabilityDenied
from .freeze import CapabilityOverrides
from .contracts import ToolContract, ToolManifest
from .ir import CallStep, HUMAN_GATE_TOOL, Node, SubStep, ThinkStep, toolref_key
from .kinds import ContextScope, Effect, Idempotency, Op
from .validate import Diagnostic


@dataclass(frozen=True)
class Budget:
    usd: Optional[float] = None
    tokens: Optional[int] = None
    wall_seconds: Optional[int] = None

    @staticmethod
    def from_dict(d: Optional[dict[str, Any]]) -> Optional["Budget"]:
        if not d:
            return None
        return Budget(usd=d.get("usd"), tokens=d.get("tokens"),
                      wall_seconds=d.get("wallSeconds") or d.get("wall_seconds"))


@dataclass(frozen=True)
class ToolGrant:
    """A granted tool. When both ``effect`` and ``idempotency`` are present the
    contract is *asserted* and overrides any MCP-hint default at freeze."""

    name: str  # toolref key: native name, or "server/tool" for MCP
    effect: Optional[Effect] = None
    idempotency: Optional[Idempotency] = None
    approval: Optional[bool] = None
    max_calls: Optional[int] = None

    @property
    def asserts_contract(self) -> bool:
        return self.effect is not None and self.idempotency is not None

    def contract(self) -> Optional[ToolContract]:
        if not self.asserts_contract:
            return None
        assert self.effect is not None and self.idempotency is not None
        return ToolContract(effect=self.effect, idempotency=self.idempotency)


@dataclass
class CapabilityManifest:
    tools: dict[str, ToolGrant] = field(default_factory=dict)
    brains: set[str] = field(default_factory=set)
    subflows: set[str] = field(default_factory=set)
    memory: set[ContextScope] = field(default_factory=set)
    network: set[str] = field(default_factory=set)     # allowed egress domains
    mcp_servers: dict[str, Optional[str]] = field(default_factory=dict)  # server -> version pin
    budget: Optional[Budget] = None
    # Section presence flags, so "absent" (unconstrained) is distinguishable from
    # "present but empty" (deny-all).
    _has_tools: bool = False
    _has_brains: bool = False
    _has_subflows: bool = False
    _has_memory: bool = False
    _has_network: bool = False
    _has_servers: bool = False

    # ----- construction ----------------------------------------------------- #
    @staticmethod
    def from_dict(d: dict[str, Any]) -> "CapabilityManifest":
        def approval_value(raw: Any) -> bool:
            if isinstance(raw, str):
                return raw.lower() in {"1", "true", "yes", "required"}
            return bool(raw)

        has_tools = "tools" in d
        tools: dict[str, ToolGrant] = {}
        for t in d.get("tools", []) or []:
            name = t["name"]
            max_calls = t["maxCalls"] if "maxCalls" in t else t.get("max_calls")
            tools[name] = ToolGrant(
                name=name,
                effect=Effect(t["effect"]) if t.get("effect") else None,
                idempotency=Idempotency(t["idempotency"]) if t.get("idempotency") else None,
                approval=approval_value(t["approval"]) if "approval" in t else None,
                max_calls=int(max_calls) if max_calls is not None else None,
            )

        has_brains = "brains" in d or "models" in d
        has_subflows = "subflows" in d or "subFlows" in d
        has_memory = "memory" in d
        has_network = "network" in d
        has_servers = "mcp_servers" in d or "mcpServers" in d
        brains_raw = d.get("brains", d.get("models", [])) or []
        subflows_raw = d.get("subflows", d.get("subFlows", [])) or []
        servers_raw = d.get("mcp_servers", d.get("mcpServers", {})) or {}

        return CapabilityManifest(
            tools=tools,
            brains=set(brains_raw),
            subflows=set(subflows_raw),
            memory={ContextScope(s) for s in (d.get("memory", []) or [])},
            network=set(d.get("network", []) or []),
            mcp_servers={k: v for k, v in servers_raw.items()},
            budget=Budget.from_dict(d.get("budget")),
            _has_tools=has_tools,
            _has_brains=has_brains,
            _has_subflows=has_subflows,
            _has_memory=has_memory,
            _has_network=has_network,
            _has_servers=has_servers,
        )

    @staticmethod
    def from_yaml(text: str) -> "CapabilityManifest":
        try:
            import yaml  # lazy: keeps the pure core free of a YAML dependency
        except ModuleNotFoundError as e:  # pragma: no cover
            raise CapabilityDenied(
                "PyYAML is required to parse a capability manifest from YAML; "
                "install pyyaml or build a CapabilityManifest with from_dict()"
            ) from e
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise CapabilityDenied("capability manifest must be a YAML mapping")
        return CapabilityManifest.from_dict(data)

    @staticmethod
    def from_file(path: str) -> "CapabilityManifest":
        with open(path, "r", encoding="utf-8") as fh:
            return CapabilityManifest.from_yaml(fh.read())

    # ----- freeze integration ---------------------------------------------- #
    def overrides(self) -> CapabilityOverrides:
        """Asserted contracts to hand to :func:`composable_agents.freeze.freeze`."""
        contracts = {
            g.name: c
            for g in self.tools.values()
            if (c := g.contract()) is not None
        }
        return CapabilityOverrides(contracts=contracts)

    # ----- compile-time enforcement (§9, seam 1) ---------------------------- #
    def enforce_compile(self, flow: Node) -> list[Diagnostic]:
        """Diagnostics for anything the flow references but the manifest denies.

        Checks tool grants always; checks brains against ``brains``, memory
        scopes against ``memory``, and MCP servers against ``mcp_servers`` only
        when those sections are present (allow-list semantics).
        """
        out: list[Diagnostic] = []
        for n in flow.walk():
            step = n.step
            if isinstance(step, CallStep):
                key = toolref_key(step.tool)
                if self._has_tools and key not in self.tools:
                    out.append(Diagnostic("CAP_TOOL_DENIED", n.id,
                                          f"tool {key!r} is not granted by the capability manifest"))
                if self._has_servers and step.tool.kind == "mcp":
                    server = step.tool.server  # type: ignore[attr-defined]
                    if server not in self.mcp_servers:
                        out.append(Diagnostic("CAP_SERVER_DENIED", n.id,
                                              f"MCP server {server!r} is not granted"))
                ctx = step.ctx
                if self._has_memory and ctx is not None and ctx.scope not in self.memory:
                    out.append(Diagnostic("CAP_MEMORY_DENIED", n.id,
                                          f"context scope {ctx.scope.value!r} is not granted"))
            elif isinstance(step, ThinkStep):
                if self._has_brains and step.brain not in self.brains:
                    out.append(Diagnostic("CAP_MODEL_DENIED", n.id,
                                          f"brain {step.brain!r} is not granted by the manifest"))
                ctx = step.ctx
                if self._has_memory and ctx is not None and ctx.scope not in self.memory:
                    out.append(Diagnostic("CAP_MEMORY_DENIED", n.id,
                                          f"context scope {ctx.scope.value!r} is not granted"))
            elif isinstance(step, SubStep):
                if self._has_subflows and step.ref not in self.subflows:
                    out.append(Diagnostic("CAP_SUBFLOW_DENIED", n.id,
                                          f"subflow {step.ref!r} is not granted by the manifest"))
        return out

    # ----- run-time helpers (§9, seam 3) ------------------------------------ #
    def network_allows(self, domain: str) -> bool:
        """Whether a native hand may reach ``domain``."""
        if not self._has_network:
            return True
        return domain in self.network

    def assert_within_budget(self, *, usd: float = 0.0, tokens: int = 0) -> None:
        """Raise :class:`CapabilityDenied` if a running estimate exceeds budget."""
        if self.budget is None:
            return
        if self.budget.usd is not None and usd > self.budget.usd:
            raise CapabilityDenied(f"budget exceeded: ${usd:.4f} > ${self.budget.usd:.4f}")
        if self.budget.tokens is not None and tokens > self.budget.tokens:
            raise CapabilityDenied(f"budget exceeded: {tokens} > {self.budget.tokens} tokens")


def check_approval_gates(
    flow: Node,
    manifest: ToolManifest,
    capabilities: Optional[CapabilityManifest] = None,
) -> list[Diagnostic]:
    """Deploy-time dominance check for approval-required tool calls.

    A call is approval-required when its frozen contract is dangerous or its
    capability grant sets ``approval``. The check is deliberately conservative:
    only a human gate that dominates the call in the enclosing IR tree satisfies
    the requirement.
    """

    out: list[Diagnostic] = []
    gate_cache: dict[int, bool] = {}

    def is_human_gate(node: Node) -> bool:
        step = node.step
        return isinstance(step, CallStep) and toolref_key(step.tool) == HUMAN_GATE_TOOL

    def children_pair(node: Node) -> list[Node]:
        return [child for child in (node.left, node.right) if child is not None]

    def always_gates(node: Node | None) -> bool:
        if node is None:
            return False
        cache_key = id(node)
        if cache_key in gate_cache:
            return gate_cache[cache_key]

        if is_human_gate(node):
            result = True
        elif node.op == Op.SEQ:
            result = always_gates(node.left) or always_gates(node.right)
        elif node.op == Op.PAR:
            result = any(always_gates(child) for child in children_pair(node))
        elif node.op == Op.ALT:
            if node.cases is not None:
                result = (
                    all(always_gates(case) for case in node.cases.values())
                    and always_gates(node.default)
                )
            else:
                result = always_gates(node.left) and always_gates(node.right)
        else:
            result = False

        gate_cache[cache_key] = result
        return result

    def approval_required(node: Node) -> bool:
        step = node.step
        if not isinstance(step, CallStep):
            return False
        key = toolref_key(step.tool)
        if key == HUMAN_GATE_TOOL:
            return False
        if capabilities is not None:
            grant = capabilities.tools.get(key)
            if grant is not None and grant.approval is True:
                return True
        if step.frozen_hash is None:
            return False
        tool = manifest.get(step.frozen_hash)
        if tool is None:
            return False
        return tool.contract.effect == Effect.DANGEROUS

    def emit_if_ungated(node: Node, gated: bool) -> None:
        step = node.step
        if not isinstance(step, CallStep) or not approval_required(node) or gated:
            return
        key = toolref_key(step.tool)
        out.append(
            Diagnostic(
                "APPROVAL_UNGATED",
                node.id,
                f"approval-required tool {key!r} is reachable without a preceding human_gate",
            )
        )

    def walk(node: Node, gated: bool) -> None:
        if node.op == Op.SEQ:
            if node.left is not None:
                walk(node.left, gated)
            if node.right is not None:
                walk(node.right, gated or always_gates(node.left))
            return

        if node.op in {Op.PAR, Op.ITER_UP_TO, Op.EVAL_PLAN}:
            for child in (node.left, node.right, node.body, node.plan):
                if child is not None:
                    walk(child, gated)
            return

        if node.op == Op.ALT:
            if node.cases is not None:
                for child in node.cases.values():
                    walk(child, gated)
                if node.default is not None:
                    walk(node.default, gated)
            else:
                for child in children_pair(node):
                    walk(child, gated)
            return

        emit_if_ungated(node, gated)

    walk(flow, False)
    return out
