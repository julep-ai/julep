"""The capability manifest (blueprint §9).

A capability manifest is the human-authored contract that says what a deployed
flow is *allowed* to touch: which tools (and with what asserted effect /
idempotency), which reasoners, which memory scopes, which MCP servers (at which
versions), and the overall budget. It does two jobs:

1. It is the only sanctioned source of *asserted* tool contracts. ``freeze``
   trusts an MCP tool's contract only when it appears here (see
   :func:`CapabilityManifest.overrides`); otherwise the contract is defaulted
   conservatively from untrusted hints and the tool can't race (§5).
2. It is an allow-list enforced at three seams (§9): *compile* (every referenced
   tool / reasoner / server / memory scope must be granted — :func:`enforce_compile`),
   *schedule* (budget, surfaced to the agent guard and the plan estimator), and
   *run* (network egress + model allow-list, checked inside the activity).

Allow-list semantics are explicit: an **absent** section means "unconstrained";
a **present** section is a deny-by-default allow-list. So omitting ``reasoners``
permits any reasoner, but listing two reasoners forbids a third.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .contracts import ToolContract, ToolManifest
from .dotctx import get_reasoner
from .errors import CapabilityDenied
from .freeze import CapabilityOverrides
from .ir import CallStep, HUMAN_GATE_TOOL, McpTool, Node, SubStep, ThinkStep, toolref_key
from .kinds import ContextScope, Effect, Idempotency, Op
from .validate import Diagnostic


@dataclass(frozen=True)
class Budget:
    cost: Optional[float] = None
    tokens: Optional[int] = None
    wall_seconds: Optional[int] = None

    @staticmethod
    def from_dict(d: Optional[dict[str, Any]]) -> Optional["Budget"]:
        if not d:
            return None
        return Budget(cost=d.get("cost", d.get("usd")), tokens=d.get("tokens"),
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
    reasoners: set[str] = field(default_factory=set)
    models: set[str] = field(default_factory=set)
    subflows: set[str] = field(default_factory=set)
    memory: set[ContextScope] = field(default_factory=set)
    network: set[str] = field(default_factory=set)     # allowed egress domains
    mcp_servers: dict[str, Optional[str]] = field(default_factory=dict)  # server -> version pin
    budget: Optional[Budget] = None
    # Section presence flags, so "absent" (unconstrained) is distinguishable from
    # "present but empty" (deny-all).
    _has_tools: bool = False
    _has_reasoners: bool = False
    _has_models: bool = False
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

        has_reasoners = "reasoners" in d
        has_models = "models" in d
        has_subflows = "subflows" in d or "subFlows" in d
        has_memory = "memory" in d
        has_network = "network" in d
        has_servers = "mcp_servers" in d or "mcpServers" in d
        reasoners_raw = d.get("reasoners", []) or []
        models_raw = d.get("models", []) or []
        subflows_raw = d.get("subflows", d.get("subFlows", [])) or []
        servers_raw = d.get("mcp_servers", d.get("mcpServers", {})) or {}

        return CapabilityManifest(
            tools=tools,
            reasoners=set(reasoners_raw),
            models=set(models_raw),
            subflows=set(subflows_raw),
            memory={ContextScope(s) for s in (d.get("memory", []) or [])},
            network=set(d.get("network", []) or []),
            mcp_servers={k: v for k, v in servers_raw.items()},
            budget=Budget.from_dict(d.get("budget")),
            _has_tools=has_tools,
            _has_reasoners=has_reasoners,
            _has_models=has_models,
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

    def to_json(self) -> dict[str, Any]:
        def tool_grant_json(grant: ToolGrant) -> dict[str, Any]:
            out: dict[str, Any] = {"name": grant.name}
            if grant.effect is not None:
                out["effect"] = grant.effect.value
            if grant.idempotency is not None:
                out["idempotency"] = grant.idempotency.value
            if grant.approval is not None:
                out["approval"] = grant.approval
            if grant.max_calls is not None:
                out["maxCalls"] = grant.max_calls
            return out

        out: dict[str, Any] = {
            "tools": [tool_grant_json(self.tools[name]) for name in sorted(self.tools)],
            "network": sorted(self.network),
            "mcpServers": {
                server: self.mcp_servers[server]
                for server in sorted(self.mcp_servers)
            },
        }
        if self._has_reasoners:
            out["reasoners"] = sorted(self.reasoners)
        if self._has_models:
            out["models"] = sorted(self.models)
        if self._has_subflows:
            out["subflows"] = sorted(self.subflows)
        if self._has_memory:
            out["memory"] = sorted(scope.value for scope in self.memory)
        if self.budget is not None:
            budget: dict[str, Any] = {}
            if self.budget.cost is not None:
                budget["cost"] = self.budget.cost
            if self.budget.tokens is not None:
                budget["tokens"] = self.budget.tokens
            if self.budget.wall_seconds is not None:
                budget["wallSeconds"] = self.budget.wall_seconds
            out["budget"] = budget
        return out

    # ----- freeze integration ---------------------------------------------- #
    def overrides(self) -> CapabilityOverrides:
        """Asserted contracts to tool to :func:`composable_agents.freeze.freeze`."""
        contracts = {
            g.name: c
            for g in self.tools.values()
            if (c := g.contract()) is not None
        }
        return CapabilityOverrides(contracts=contracts)

    def max_call_limits(self) -> dict[str, int]:
        """Per-tool maxCalls limits keyed by capability tool ref."""
        return {
            name: grant.max_calls
            for name, grant in self.tools.items()
            if grant.max_calls is not None
        }

    # ----- compile-time enforcement (§9, seam 1) ---------------------------- #
    def enforce_compile(
        self,
        flow: Node,
        manifest: Optional[ToolManifest] = None,
    ) -> list[Diagnostic]:
        """Diagnostics for anything the flow references but the manifest denies.

        Checks tool grants always; checks reasoners against ``reasoners``, resolved
        model ids against ``models``, memory scopes against ``memory``, and MCP
        servers/pins against ``mcp_servers`` only when those sections are
        present (allow-list semantics). If a reasoner is not registered, model-id
        enforcement skips it because there is no resolved model id to compare.
        """
        out: list[Diagnostic] = []
        for n in flow.walk():
            step = n.step
            if isinstance(step, CallStep):
                key = toolref_key(step.tool)
                if self._has_tools and key not in self.tools:
                    out.append(Diagnostic("CAP_TOOL_DENIED", n.id,
                                          f"tool {key!r} is not granted by the capability manifest"))
                if self._has_servers and isinstance(step.tool, McpTool):
                    server = step.tool.server
                    if server not in self.mcp_servers:
                        out.append(Diagnostic("CAP_SERVER_DENIED", n.id,
                                              f"MCP server {server!r} is not granted"))
                    else:
                        pin = self.mcp_servers[server]
                        if pin is not None:
                            version = _server_version(step, manifest)
                            if not _version_satisfies(version, pin):
                                actual = version if version is not None else "<unversioned>"
                                out.append(Diagnostic(
                                    "CAP_VERSION_PIN",
                                    n.id,
                                    f"MCP server {server!r} version {actual!r} "
                                    f"does not satisfy pin {pin!r}",
                                ))
                ctx = step.ctx
                if self._has_memory and ctx is not None and ctx.scope not in self.memory:
                    out.append(Diagnostic("CAP_MEMORY_DENIED", n.id,
                                          f"context scope {ctx.scope.value!r} is not granted"))
            for reasoner in _reasoner_refs(n):
                if self._has_reasoners and reasoner not in self.reasoners:
                    out.append(Diagnostic("CAP_MODEL_DENIED", n.id,
                                          f"reasoner {reasoner!r} is not granted by the manifest"))
                if self._has_models:
                    try:
                        model = get_reasoner(reasoner).model
                    except KeyError:
                        model = None
                    if model is not None and model not in self.models:
                        out.append(Diagnostic(
                            "CAP_MODEL_ID_DENIED",
                            n.id,
                            f"reasoner {reasoner!r} resolves to model {model!r}, "
                            "which is not granted by the manifest",
                        ))
            if isinstance(step, ThinkStep):
                ctx = step.ctx
                if self._has_memory and ctx is not None and ctx.scope not in self.memory:
                    out.append(Diagnostic("CAP_MEMORY_DENIED", n.id,
                                          f"context scope {ctx.scope.value!r} is not granted"))
            elif isinstance(step, SubStep):
                if self._has_subflows and step.ref not in self.subflows:
                    out.append(Diagnostic("CAP_SUBFLOW_DENIED", n.id,
                                          f"subflow {step.ref!r} is not granted by the manifest"))
            if n.op == Op.APP:
                if n.tools is not None:
                    for key in n.tools:
                        tool_key = str(key)
                        if self._has_tools and tool_key not in self.tools:
                            out.append(Diagnostic(
                                "CAP_APP_TOOL_DENIED",
                                n.id,
                                f"app inline tool {tool_key!r} is not granted by the capability manifest",
                            ))
                        if self._app_tool_approval_required(tool_key, manifest):
                            out.append(Diagnostic(
                                "CAP_APP_APPROVAL_TOOL",
                                n.id,
                                f"app inline tool {tool_key!r} requires approval and cannot be called by an agent",
                            ))
                if n.subflows is not None and self._has_subflows:
                    for ref in n.subflows:
                        subflow_ref = str(ref)
                        if subflow_ref not in self.subflows:
                            out.append(Diagnostic(
                                "CAP_APP_SUBFLOW_DENIED",
                                n.id,
                                f"app inline subflow {subflow_ref!r} is not granted by the capability manifest",
                            ))
        return out

    def _app_tool_approval_required(
        self,
        tool_key: str,
        manifest: Optional[ToolManifest],
    ) -> bool:
        grant = self.tools.get(tool_key)
        if grant is not None:
            if grant.approval is True or grant.effect == Effect.DANGEROUS:
                return True
        if manifest is not None:
            for frozen in manifest.values():
                if toolref_key(frozen.ref) == tool_key and frozen.contract.effect == Effect.DANGEROUS:
                    return True
        return False

    # ----- run-time helpers (§9, seam 3) ------------------------------------ #
    def network_allows(self, domain: str) -> bool:
        """Whether a native tool may reach ``domain``."""
        if not self._has_network:
            return True
        return domain in self.network

    def assert_within_budget(self, *, cost: float = 0.0, tokens: int = 0) -> None:
        """Raise :class:`CapabilityDenied` if a running estimate exceeds budget."""
        if self.budget is None:
            return
        if self.budget.cost is not None and cost > self.budget.cost:
            raise CapabilityDenied(f"cost budget exceeded: {cost:.4f} > {self.budget.cost:.4f}")
        if self.budget.tokens is not None and tokens > self.budget.tokens:
            raise CapabilityDenied(f"budget exceeded: {tokens} > {self.budget.tokens} tokens")


def _reasoner_refs(node: Node) -> list[str]:
    refs: list[str] = []
    step = node.step
    if isinstance(step, ThinkStep):
        refs.append(step.reasoner)
    if node.op in (Op.APP, Op.EVAL_PLAN) and node.controller is not None:
        refs.append(node.controller)
    return refs


def _server_version(step: CallStep, manifest: Optional[ToolManifest]) -> Optional[str]:
    if manifest is None or step.frozen_hash is None:
        return None
    tool = manifest.get(step.frozen_hash)
    return tool.server_version if tool is not None else None


_VERSION_CONSTRAINT = re.compile(r"^\s*(>=|<=|==|>|<)?\s*(.+?)\s*$")


def _version_tokens(version: str) -> list[tuple[int, int | str]]:
    tokens: list[tuple[int, int | str]] = []
    for part in str(version).strip().split("."):
        for chunk in re.findall(r"\d+|[^\d]+", part):
            if chunk.isdigit():
                tokens.append((0, int(chunk)))
            else:
                tokens.append((1, chunk))
    while tokens and tokens[-1] == (0, 0):
        tokens.pop()
    return tokens


def _compare_versions(left: str, right: str) -> int:
    left_tokens = _version_tokens(left)
    right_tokens = _version_tokens(right)
    size = max(len(left_tokens), len(right_tokens))
    for i in range(size):
        l_token = left_tokens[i] if i < len(left_tokens) else (0, 0)
        r_token = right_tokens[i] if i < len(right_tokens) else (0, 0)
        if l_token < r_token:
            return -1
        if l_token > r_token:
            return 1
    return 0


def _version_satisfies(actual: Optional[str], constraint: str) -> bool:
    if actual is None:
        return False
    match = _VERSION_CONSTRAINT.match(str(constraint))
    if match is None:
        return False
    op = match.group(1) or "=="
    expected = match.group(2)
    cmp = _compare_versions(actual, expected)
    if op == "==":
        return cmp == 0
    if op == ">=":
        return cmp >= 0
    if op == ">":
        return cmp > 0
    if op == "<=":
        return cmp <= 0
    if op == "<":
        return cmp < 0
    return False


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
                    and (node.default is None or always_gates(node.default))
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

        if node.op in {Op.PAR, Op.EACH, Op.ITER_UP_TO, Op.EVAL_PLAN}:
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
