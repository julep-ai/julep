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
a **present** section is a deny-by-default allow-list. So omitting ``models``
permits any brain, but listing two brains forbids a third.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .errors import CapabilityDenied
from .freeze import CapabilityOverrides
from .ir import CallStep, Node, SubStep, ThinkStep, toolref_key
from .kinds import ContextScope, Effect, Idempotency
from .contracts import ToolContract
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
    models: set[str] = field(default_factory=set)      # empty => unconstrained
    memory: set[ContextScope] = field(default_factory=set)  # empty => unconstrained
    network: set[str] = field(default_factory=set)     # allowed egress domains
    mcp_servers: dict[str, Optional[str]] = field(default_factory=dict)  # server -> version pin
    budget: Optional[Budget] = None
    # Section presence flags, so "absent" (unconstrained) is distinguishable from
    # "present but empty" (deny-all).
    _has_models: bool = False
    _has_memory: bool = False
    _has_servers: bool = False

    # ----- construction ----------------------------------------------------- #
    @staticmethod
    def from_dict(d: dict[str, Any]) -> "CapabilityManifest":
        tools: dict[str, ToolGrant] = {}
        for t in d.get("tools", []) or []:
            name = t["name"]
            tools[name] = ToolGrant(
                name=name,
                effect=Effect(t["effect"]) if t.get("effect") else None,
                idempotency=Idempotency(t["idempotency"]) if t.get("idempotency") else None,
                max_calls=t.get("maxCalls") or t.get("max_calls"),
            )

        has_models = "models" in d
        has_memory = "memory" in d
        has_servers = "mcp_servers" in d or "mcpServers" in d
        servers_raw = d.get("mcp_servers", d.get("mcpServers", {})) or {}

        return CapabilityManifest(
            tools=tools,
            models=set(d.get("models", []) or []),
            memory={ContextScope(s) for s in (d.get("memory", []) or [])},
            network=set(d.get("network", []) or []),
            mcp_servers={k: v for k, v in servers_raw.items()},
            budget=Budget.from_dict(d.get("budget")),
            _has_models=has_models,
            _has_memory=has_memory,
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

        Checks tool grants always; checks brains against ``models``, memory
        scopes against ``memory``, and MCP servers against ``mcp_servers`` only
        when those sections are present (allow-list semantics).
        """
        out: list[Diagnostic] = []
        for n in flow.walk():
            step = n.step
            if isinstance(step, CallStep):
                key = toolref_key(step.tool)
                if key not in self.tools:
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
                if self._has_models and step.brain not in self.models:
                    out.append(Diagnostic("CAP_MODEL_DENIED", n.id,
                                          f"brain {step.brain!r} is not granted by the manifest"))
                ctx = step.ctx
                if self._has_memory and ctx is not None and ctx.scope not in self.memory:
                    out.append(Diagnostic("CAP_MEMORY_DENIED", n.id,
                                          f"context scope {ctx.scope.value!r} is not granted"))
            # SubStep: the child has its own manifest; nothing to check at the
            # surface beyond the contract carried on the SubContract.
        return out

    # ----- run-time helpers (§9, seam 3) ------------------------------------ #
    def network_allows(self, domain: str) -> bool:
        """Whether a native hand may reach ``domain`` (empty allow-list => any)."""
        if not self.network:
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
