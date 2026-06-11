"""Small facade helpers for native Python-callable tools and agents."""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import types
import warnings
from collections.abc import Mapping as AbcMapping
from collections.abc import Sequence as AbcSequence
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from .agent_loop import AgentConfig, drive_agent_loop
from .capabilities import Budget, CapabilityManifest, ToolGrant
from .contracts import ToolContract
from .deploy import Deployment, deploy
from .dotctx import Brain, register_brain
from .dsl import app, call, native
from .errors import ValidationError
from .execution.cma import CMAAgentEnv, CMAClient, manifest_to_custom_tools
from .execution.interpreter import InMemoryEnv, interpret
from .freeze import McpSnapshot, NativeToolSpec
from .typed import Flow, FlowLike, SplitCapability
from .flow_registry import register_flow
from .ir import HUMAN_GATE_TOOL, JSONSchema, Node, canonical_json, toolref_key
from .kinds import Effect, EnforcementMode, Idempotency
from .projection import InMemoryProjection, ProjectionEmitter
from .result import Result
from .validate import Diagnostic, blocking

_OBJECT_SCHEMA: JSONSchema = {"type": "object"}
_ALLOWED_EFFECTS = ("read", "write", "external", "dangerous")
_NONE_TYPE = type(None)
In = TypeVar("In")
Out = TypeVar("Out")

AGENT_REPLY_SCHEMA: JSONSchema = {
    "oneOf": [
        {
            "type": "object",
            "required": ["tool"],
            "properties": {
                "tool": {"type": "string"},
                "input": {},
            },
            "additionalProperties": False,
        },
        {
            "type": "object",
            "required": ["sub"],
            "properties": {
                "sub": {"type": "string"},
                "input": {},
            },
            "additionalProperties": False,
        },
        {
            "type": "object",
            "required": ["output"],
            "properties": {
                "output": {},
            },
            "additionalProperties": False,
        },
        {
            "type": "object",
            "required": ["done"],
            "properties": {
                "done": {"const": True},
                "output": {},
            },
            "additionalProperties": False,
        },
        {
            "type": "object",
            "required": ["escalate"],
            "properties": {
                "escalate": {"type": "string"},
            },
            "additionalProperties": False,
        },
    ]
}

_DEFAULT_LOCAL_BRAIN_WARNING = (
    "Agent llm=None: no model configured; returning input unprocessed. "
    "Pass llm= for real behavior."
)
_default_local_brain_warned = False
_KEEP: Any = object()


def default_local_brain(_brain_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Keyless demo brain: terminal, explicit, and never silently intelligent."""
    global _default_local_brain_warned
    if not _default_local_brain_warned:
        warnings.warn(_DEFAULT_LOCAL_BRAIN_WARNING, RuntimeWarning, stacklevel=2)
        _default_local_brain_warned = True
    return {
        "output": {
            "note": (
                "no model configured (llm=None); returning input unprocessed "
                "- pass llm= for real behavior"
            ),
            "input": payload.get("input"),
        }
    }


def _copy_schema(schema: JSONSchema) -> JSONSchema:
    return dict(schema)


def python_type_to_schema(tp: object) -> JSONSchema:
    """Map a small, total subset of Python types to JSON Schema."""
    if tp is Any or tp is inspect.Signature.empty:
        return _copy_schema(_OBJECT_SCHEMA)
    if tp is str:
        return {"type": "string"}
    if tp is bool:
        return {"type": "boolean"}
    if tp is int:
        return {"type": "integer"}
    if tp is float:
        return {"type": "number"}
    if tp is dict or tp is AbcMapping:
        return _copy_schema(_OBJECT_SCHEMA)

    origin = get_origin(tp)
    args = get_args(tp)

    if origin in {Union, types.UnionType}:
        non_none = tuple(arg for arg in args if arg is not _NONE_TYPE)
        if len(non_none) == 1:
            return python_type_to_schema(non_none[0])
        return _copy_schema(_OBJECT_SCHEMA)

    if origin in {dict, AbcMapping}:
        return _copy_schema(_OBJECT_SCHEMA)

    if origin in {list, AbcSequence}:
        if not args:
            return {"type": "array"}
        return {"type": "array", "items": python_type_to_schema(args[0])}

    return _copy_schema(_OBJECT_SCHEMA)


def _effect_from_string(effect: str) -> Effect:
    try:
        return Effect(effect)
    except ValueError as exc:
        allowed = ", ".join(_ALLOWED_EFFECTS)
        raise ValueError(f"invalid effect {effect!r}; allowed values: {allowed}") from exc


def _schema_from_hints(fn: Callable[..., Any]) -> tuple[JSONSchema, JSONSchema, tuple[str, ...]]:
    try:
        hints = get_type_hints(fn)
    except Exception:
        hints = {}

    signature = inspect.signature(fn)
    positional = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }
    ]
    output_type = hints.get("return", signature.return_annotation)
    output_schema = python_type_to_schema(output_type)

    if len(positional) <= 1:
        if positional:
            parameter = positional[0]
            input_type = hints.get(parameter.name, parameter.annotation)
        else:
            input_type = inspect.Signature.empty
        input_schema = python_type_to_schema(input_type)
    else:
        properties = {
            parameter.name: python_type_to_schema(hints.get(parameter.name, parameter.annotation))
            for parameter in positional
        }
        required = [
            parameter.name
            for parameter in positional
            if parameter.default is inspect.Parameter.empty
        ]
        input_schema = {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    param_names = tuple(parameter.name for parameter in positional)
    return input_schema, output_schema, param_names


@dataclass(frozen=True)
class Tool(FlowLike[In, Out]):
    name: str
    fn: Callable[..., Out]
    contract: ToolContract
    input_schema: JSONSchema
    output_schema: JSONSchema
    param_names: tuple[str, ...] = ()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        from .define import apply_if_authoring

        authored = apply_if_authoring(self, args, kwargs)
        if authored is not NotImplemented:
            return authored
        return self.fn(*args, **kwargs)

    def to_ir(self) -> Node:
        return call(native(self.name))

    @property
    def bound_hand(self) -> Callable[[Any], Any]:
        """Hand wrapper for the single threaded value: positional-only params are
        passed positionally (declared order), the rest by keyword."""
        if len(self.param_names) <= 1:
            return self.fn
        fn = self.fn
        positional_only = tuple(
            parameter.name
            for parameter in inspect.signature(fn).parameters.values()
            if parameter.kind is inspect.Parameter.POSITIONAL_ONLY
        )

        def _hand(value: Any) -> Any:
            args = [value[name] for name in positional_only if name in value]
            kwargs = {key: item for key, item in value.items() if key not in positional_only}
            return fn(*args, **kwargs)

        return _hand

    @property
    def native_spec(self) -> NativeToolSpec:
        return NativeToolSpec(
            input_schema=self.input_schema,
            contract=self.contract,
            output_schema=self.output_schema,
        )


def _build_tool(
    fn: Callable[..., Any],
    *,
    effect: Effect,
    idempotent: bool,
    name: Optional[str],
) -> Tool[Any, Any]:
    input_schema, output_schema, param_names = _schema_from_hints(fn)
    return Tool(
        name=name or fn.__name__,
        fn=fn,
        contract=ToolContract(
            effect=effect,
            idempotency=Idempotency.NATIVE if idempotent else Idempotency.NONE,
        ),
        input_schema=input_schema,
        output_schema=output_schema,
        param_names=param_names,
    )


def cma_tool_binding(native_tool: Tool[Any, Any]) -> tuple[JSONSchema, Callable[[Any], Any]]:
    """Bridge one native tool to the CMA custom-tool calling convention.

    CMA requires every custom tool's ``input_schema`` to be a JSON object and the
    hosted model emits a named-argument object (e.g. ``{"city": "Tokyo"}``). The
    framework's native model threads a single value, so a single scalar-arg tool
    has a non-object schema and a hand expecting the bare value. This returns the
    CMA-valid object schema plus a hand that translates the model's argument
    object back to the framework's threaded value. Multi-arg / already-object
    tools pass through unchanged (``bound_hand`` already unpacks the object).
    """
    schema = native_tool.input_schema
    bound = native_tool.bound_hand

    if not native_tool.param_names:
        # Zero-argument tool: CMA still requires an object schema and emits an
        # object (typically {}); the hand takes no value, so ignore the input.
        zero_fn = native_tool.fn
        zero_schema: JSONSchema = (
            schema if isinstance(schema, dict) and schema.get("type") == "object" else _OBJECT_SCHEMA
        )

        def adapt_zero(_value: Any) -> Any:
            return zero_fn()

        return zero_schema, adapt_zero

    if isinstance(schema, dict) and schema.get("type") == "object":
        return schema, bound

    param_name = native_tool.param_names[0]
    wrapped: JSONSchema = {
        "type": "object",
        "properties": {param_name: schema},
        "required": [param_name],
        "additionalProperties": False,
    }

    def adapt(value: Any) -> Any:
        if isinstance(value, AbcMapping) and param_name in value:
            return bound(value[param_name])
        return bound(value)

    return wrapped, adapt


@overload
def tool(fn: Callable[[In], Out], /) -> Tool[In, Out]:
    ...


@overload
def tool(fn: Callable[..., Out], /) -> Tool[Any, Out]:
    ...


@overload
def tool(
    fn: None = None,
    /,
    *,
    effect: str = "write",
    idempotent: bool = False,
    name: Optional[str] = None,
) -> Callable[[Callable[..., Out]], Tool[Any, Out]]:
    ...


def tool(
    fn: Optional[Callable[..., Any]] = None,
    /,
    *,
    effect: str = "write",
    idempotent: bool = False,
    name: Optional[str] = None,
) -> Tool[Any, Any] | Callable[[Callable[..., Any]], Tool[Any, Any]]:
    mapped_effect = _effect_from_string(effect)

    def decorate(inner: Callable[..., Any]) -> Tool[Any, Any]:
        return _build_tool(inner, effect=mapped_effect, idempotent=idempotent, name=name)

    if fn is not None:
        return decorate(fn)
    return decorate


def snapshot_from_tools(tools: Sequence[Tool[Any, Any]]) -> McpSnapshot:
    return McpSnapshot(native={native_tool.name: native_tool.native_spec for native_tool in tools})


def _derive_agent_name(
    *,
    model: str,
    tool_names: tuple[str, ...],
    budget_cost: Optional[float],
    max_rounds: int,
    instructions: str,
) -> str:
    payload = canonical_json(
        {
            "budget_cost": budget_cost,
            "instructions": instructions,
            "max_rounds": max_rounds,
            "model": model,
            "tools": list(tool_names),
        }
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
    return f"agent-{digest}"


class Agent(FlowLike[Any, Any]):
    """Thin facade over the existing APP IR, local interpreter, and deployment."""

    _name: str

    def __init__(
        self,
        brain: str,
        tools: Sequence[FlowLike[Any, Any] | SplitCapability] = (),
        *,
        name: Optional[str] = None,
        llm: Optional[Callable[[str, Any], Any]] = None,
        budget_cost: Optional[float] = None,
        max_rounds: int = 24,
        instructions: Optional[str] = None,
        mode: EnforcementMode | str = EnforcementMode.STRICT,
    ) -> None:
        """Create an agent facade.

        When ``name`` is omitted, the controller name is derived from the agent
        config. An explicit ``name`` is used unchanged and must be unique per
        distinct agent config in the current process.
        """
        caps = tuple(tools)
        tool_caps: list[Tool[Any, Any]] = []
        flow_cap_pairs: list[tuple[str, FlowLike[Any, Any]]] = []
        split_children: dict[str, SplitCapability] = {}
        for cap in caps:
            if isinstance(cap, SplitCapability):
                flow_cap_pairs.append((cap.ref, cap.target))
                split_children[cap.ref] = cap
            elif isinstance(cap, Tool):
                tool_caps.append(cap)
            elif isinstance(cap, Agent):
                flow_cap_pairs.append((cap._name, cap))
            elif isinstance(cap, Flow):
                if cap.name is None:
                    raise ValidationError(
                        [
                            Diagnostic(
                                "CAP_APP_FLOW_UNNAMED",
                                "app",
                                "a flow used as an agent capability must be .named(ref)",
                            )
                        ]
                    )
                flow_cap_pairs.append((cap.name, cap))
            else:
                raise TypeError(
                    "agent capability must be a Tool, Flow, or Agent; "
                    f"got {type(cap).__name__}"
                )
        tool_names = tuple(native_tool.name for native_tool in tool_caps)
        sub_refs = tuple(ref for ref, _ in flow_cap_pairs)
        system = instructions or ""
        if name is None:
            resolved_name = _derive_agent_name(
                model=brain,
                tool_names=tool_names,
                budget_cost=budget_cost,
                max_rounds=max_rounds,
                instructions=system,
            )
        else:
            resolved_name = name
        self._name = resolved_name
        self._brain_model = brain
        self._caps = caps
        self._tools = tuple(tool_caps)
        self._flow_caps: dict[str, FlowLike[Any, Any]] = {
            ref: cap for ref, cap in flow_cap_pairs
        }
        self._split_children: dict[str, SplitCapability] = dict(split_children)
        self._tool_names = tool_names
        self._sub_refs = sub_refs
        self._llm = llm
        self._budget_cost = budget_cost
        self._max_rounds = max_rounds
        self._instructions = instructions
        self._brain_fn = llm or default_local_brain
        self._budget = Budget(cost=budget_cost) if budget_cost is not None else None
        self._mode = EnforcementMode.coerce(mode)
        self._cfg = AgentConfig(max_rounds=max_rounds, budget=self._budget, mode=self._mode)
        self._granted = {native_tool.name for native_tool in self._tools}
        self._contracts = {
            native_tool.name: {
                "effect": native_tool.contract.effect.value,
                "idempotency": native_tool.contract.idempotency.value,
            }
            for native_tool in self._tools
        }

        for ref, cap in flow_cap_pairs:
            if isinstance(cap, Flow):
                register_flow(ref, cap)

        register_brain(
            Brain(
                name=resolved_name,
                model=brain,
                system=system,
                reply_schema=AGENT_REPLY_SCHEMA,
                tools=tool_names,
                is_agent=True,
            )
        )
        self._flow = app(
            resolved_name,
            tools=list(tool_names),
            subflows=(list(sub_refs) or None),
            budget=self._budget,
            max_rounds=max_rounds,
        )
        self._snapshot = snapshot_from_tools(self._tools)
        self._capabilities = CapabilityManifest(
            tools={
                native_tool.name: ToolGrant(
                    name=native_tool.name,
                    effect=native_tool.contract.effect,
                    idempotency=native_tool.contract.idempotency,
                )
                for native_tool in self._tools
            },
            budget=self._budget,
            subflows=set(sub_refs),
            _has_tools=True,
            _has_subflows=bool(sub_refs),
        )
        self._deployment_cache: Optional[Deployment] = None
        self._deployment_base_diagnostics: list[Diagnostic] = []
        self._plain_flow_deployment_cache: dict[str, Deployment] = {}
        self._eager_capability_checks()

    def to_ir(self) -> Node:
        return self._flow

    def _durable_ref(self) -> Optional[str]:
        return self._name

    def _params(self) -> dict[str, Any]:
        return {
            "brain": self._brain_model,
            "tools": list(self._caps),
            "llm": self._llm,
            "budget_cost": self._budget_cost,
            "max_rounds": self._max_rounds,
            "instructions": self._instructions,
            "mode": self._mode,
        }

    def _reconstruct(self, **overrides: Any) -> "Agent":
        params = self._params()
        params.update(overrides)
        brain = params.pop("brain")
        return Agent(brain, name=None, **params)

    @staticmethod
    def _cap_name(cap: FlowLike[Any, Any] | SplitCapability) -> Optional[str]:
        if isinstance(cap, SplitCapability):
            return cap.ref
        if isinstance(cap, Tool):
            return cap.name
        if isinstance(cap, Agent):
            return cap._name
        if isinstance(cap, Flow):
            return cap.name
        return None

    def with_tools(
        self,
        *,
        add: Sequence[FlowLike[Any, Any] | SplitCapability] = (),
        remove: Sequence[FlowLike[Any, Any] | SplitCapability | str] = (),
    ) -> "Agent":
        removed = {
            cap if isinstance(cap, str) else self._cap_name(cap)
            for cap in remove
        }
        kept = [cap for cap in self._caps if self._cap_name(cap) not in removed]
        return self._reconstruct(tools=[*kept, *add])

    def without(self, *tools: FlowLike[Any, Any] | SplitCapability | str) -> "Agent":
        names = {
            cap if isinstance(cap, str) else self._cap_name(cap)
            for cap in tools
        }
        return self._reconstruct(
            tools=[cap for cap in self._caps if self._cap_name(cap) not in names]
        )

    def replace(
        self,
        *,
        brain: Optional[str] = None,
        budget_cost: Any = _KEEP,
        max_rounds: Optional[int] = None,
        instructions: Any = _KEEP,
        mode: Any = _KEEP,
        llm: Any = _KEEP,
    ) -> "Agent":
        overrides: dict[str, Any] = {}
        if brain is not None:
            overrides["brain"] = brain
        if max_rounds is not None:
            overrides["max_rounds"] = max_rounds
        if budget_cost is not _KEEP:
            overrides["budget_cost"] = budget_cost
        if instructions is not _KEEP:
            overrides["instructions"] = instructions
        if mode is not _KEEP:
            overrides["mode"] = mode
        if llm is not _KEEP:
            overrides["llm"] = llm
        return self._reconstruct(**overrides)

    def _plain_flow_cap_deployments(self, *, strict: bool) -> dict[str, Deployment]:
        deployments: dict[str, Deployment] = {}
        strict_bad: list[Diagnostic] = []
        for ref, cap in self._flow_caps.items():
            if isinstance(cap, Agent):
                continue
            cached = self._plain_flow_deployment_cache.get(ref)
            if cached is None:
                cached = deploy(
                    cap.to_ir(),
                    self._snapshot,
                    capabilities=self._capabilities,
                    strict=strict,
                    mode=self._mode,
                )
                self._plain_flow_deployment_cache[ref] = cached
            deployments[ref] = cached
            if strict and self._mode is EnforcementMode.STRICT:
                strict_bad.extend(blocking(cached.diagnostics))
        if strict_bad:
            raise ValidationError(strict_bad)
        return deployments

    def _deploy(self, *, strict: bool = True) -> Deployment:
        if self._deployment_cache is None:
            self._deployment_cache = deploy(
                self._flow,
                self._snapshot,
                capabilities=self._capabilities,
                strict=strict,
                mode=self._mode,
            )
            self._deployment_base_diagnostics = list(self._deployment_cache.diagnostics)
        elif strict and self._mode is EnforcementMode.STRICT:
            bad = blocking(self._deployment_base_diagnostics)
            if bad:
                raise ValidationError(bad)
        cap_deployments = self._plain_flow_cap_deployments(strict=strict)
        cap_diagnostics = [
            diagnostic
            for cap_deployment in cap_deployments.values()
            for diagnostic in cap_deployment.diagnostics
        ]
        self._deployment_cache.diagnostics = [
            *self._deployment_base_diagnostics,
            *cap_diagnostics,
        ]
        return self._deployment_cache

    def _eager_capability_checks(self) -> None:
        tool_names = list(self._tool_names)
        sub_refs = list(self._sub_refs)
        dup_tools = {name for name in tool_names if tool_names.count(name) > 1}
        dup_subs = {ref for ref in sub_refs if sub_refs.count(ref) > 1}
        overlap = set(tool_names) & set(sub_refs)
        collisions = sorted(dup_tools | dup_subs | overlap)
        if collisions:
            raise ValidationError(
                [
                    Diagnostic(
                        "CAP_APP_TOOL_COLLISION",
                        self._flow.id,
                        f"capability name {name!r} collides: tool and subflow names "
                        "must be unique within an agent",
                    )
                    for name in collisions
                ]
            )
        if self._mode is EnforcementMode.STRICT:
            dangerous = [
                native_tool.name
                for native_tool in self._tools
                if native_tool.contract.effect == Effect.DANGEROUS
            ]
            if dangerous:
                raise ValidationError(
                    [
                        Diagnostic(
                            "CAP_APP_APPROVAL_TOOL",
                            self._flow.id,
                            f"app inline tool {name!r} requires approval and cannot "
                            "be called by an agent",
                        )
                        for name in dangerous
                    ]
                )
        granted = set(self._tool_names)
        for ref, cap in self._flow_caps.items():
            if isinstance(cap, Agent):
                continue
            for tref in cap.to_ir().tool_refs():
                key = toolref_key(tref)
                if key == HUMAN_GATE_TOOL:
                    continue
                if key not in granted:
                    raise ValidationError(
                        [
                            Diagnostic(
                                "CAP_APP_FLOW_UNGRANTED_TOOL",
                                self._flow.id,
                                f"plain Flow capability {ref!r} calls tool {key!r} which "
                                "the agent does not grant; a plain Flow capability may "
                                "only call the agent's own granted tools - for a "
                                "capability with its own tools, pass an Agent",
                            )
                        ]
                    )

    async def arun(
        self, input: Any, *, principal: Optional[dict[str, Any]] = None
    ) -> "Result[Any]":
        deployment = self._deploy()
        plain_flow_deployments = self._plain_flow_cap_deployments(strict=True)
        emitter = ProjectionEmitter(InMemoryProjection())
        tool_fns = {native_tool.name: native_tool.bound_hand for native_tool in self._tools}
        max_call_limits = (
            deployment.capabilities.max_call_limits()
            if deployment.capabilities is not None
            else {}
        )
        contracts: dict[str, dict[str, Any]] = {
            name: dict(contract) for name, contract in self._contracts.items()
        }
        for tool_name, limit in max_call_limits.items():
            contracts.setdefault(tool_name, {})["maxCalls"] = limit

        async def invoke_controller(payload: dict[str, Any]) -> Any:
            # Pass the brain *name* (not the model string): it is the registry key
            # a real llm caller resolves to recover system + reply_schema, and it
            # matches the long-documented ``_brain_name`` parameter. Scripted
            # callers ignore it, so this is behaviour-preserving for them.
            reply = self._brain_fn(self._name, payload)
            if inspect.isawaitable(reply):
                return await reply
            return reply

        async def call_tool(name: str, value: Any) -> Any:
            if name not in tool_fns:
                return {
                    "error": f"tool {name!r} unavailable (dev mode: not a registered tool of this agent)"
                }
            result = tool_fns[name](value)
            if inspect.isawaitable(result):
                return await result
            return result

        run_subflow = None
        granted_subflows = None
        if self._flow_caps:
            granted_subflows = set(self._flow_caps)

            async def run_subflow(ref: str, value: Any) -> Any:
                cap = self._flow_caps.get(ref)
                if cap is None:
                    return {"error": f"subflow {ref!r} unavailable"}
                if isinstance(cap, Agent):
                    return await cap.arun(value)
                sub_deployment = plain_flow_deployments[ref]
                sub_env = InMemoryEnv(
                    sub_deployment.manifest,
                    emitter,
                    hands=tool_fns,
                    mode=self._mode,
                )
                sub_result = await interpret(sub_deployment.flow, value, sub_env)
                return sub_result.value

        env = InMemoryEnv(
            deployment.manifest,
            emitter,
            hands=tool_fns,
            agents={
                self._name: lambda value: drive_agent_loop(
                    input=value,
                    cfg=self._cfg,
                    invoke_controller=invoke_controller,
                    call_tool=call_tool,
                    run_subflow=run_subflow,
                    granted=self._granted,
                    granted_subflows=granted_subflows,
                    contracts=contracts,
                )
            },
            max_calls=max_call_limits,
            mode=self._mode,
            principal=principal,
        )
        result = await interpret(deployment.flow, input, env)
        return Result(cast("dict[str, Any]", result.value))

    async def arun_on_cma(
        self,
        input: Any,
        *,
        client: CMAClient,
        environment: Any = None,
    ) -> "Result[Any]":
        deployment = self._deploy()
        emitter = ProjectionEmitter(InMemoryProjection())
        tool_fns = {native_tool.name: native_tool.bound_hand for native_tool in self._tools}
        max_call_limits = (
            deployment.capabilities.max_call_limits()
            if deployment.capabilities is not None
            else {}
        )
        contracts: dict[str, dict[str, Any]] = {
            name: dict(contract) for name, contract in self._contracts.items()
        }
        for tool_name, limit in max_call_limits.items():
            contracts.setdefault(tool_name, {})["maxCalls"] = limit

        # CMA needs object input schemas + named-argument objects; bind each tool
        # to that calling convention (and adapt its hand to translate back).
        cma_schemas: dict[str, JSONSchema] = {}
        cma_hands: dict[str, Callable[[Any], Any]] = {}
        for native_tool in self._tools:
            schema, hand = cma_tool_binding(native_tool)
            cma_schemas[native_tool.name] = schema
            cma_hands[native_tool.name] = hand

        custom_tools = manifest_to_custom_tools(
            self._tool_names,
            input_schemas=cma_schemas,
            descriptions={native_tool.name: native_tool.fn.__doc__ or "" for native_tool in self._tools},
        )
        inner = InMemoryEnv(
            deployment.manifest,
            emitter,
            hands=tool_fns,
            mode=self._mode,
        )
        cma_env = CMAAgentEnv(
            inner,
            client=client,
            environment=environment,
            hands=cma_hands,
            cfg=self._cfg,
            granted=self._granted,
            contracts=contracts,
            custom_tools=custom_tools,
        )
        result = await interpret(deployment.flow, input, cma_env)
        return Result(cast("dict[str, Any]", result.value))

    def run(
        self, input: Any, *, principal: Optional[dict[str, Any]] = None
    ) -> "Result[Any]":
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.arun(input, principal=principal))
        raise RuntimeError("Agent.run() cannot be called inside a running event loop; use await Agent.arun(...)")

    def run_on_cma(
        self,
        input: Any,
        *,
        client: CMAClient,
        environment: Any = None,
    ) -> "Result[Any]":
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.arun_on_cma(input, client=client, environment=environment))
        raise RuntimeError(
            "Agent.run_on_cma() cannot be called inside a running event loop; "
            "use await Agent.arun_on_cma(...)"
        )

    def deployment(self) -> Deployment:
        return self._deploy()

    def split_children(self) -> dict[str, SplitCapability]:
        """The per-component split children (ref -> marker)."""
        return dict(self._split_children)

    def sub_deployments(self) -> dict[str, "Deployment"]:
        """Compiled child deployments for this agent's sub-capabilities (ref -> Deployment).

        Plain-`Flow` capabilities are compiled through the deploy gates here;
        sub-`Agent` capabilities expose their own :meth:`deployment`. A worker
        hosting this agent on Temporal MUST be configured with these (its
        ``WorkerContext.subflows``) so a ``SUB`` decision resolves to the
        validated/frozen child artifact rather than a stale/missing one.
        (Auto-wiring this into :meth:`deploy` is a documented follow-on seam.)
        """
        out: dict[str, Deployment] = dict(self._plain_flow_cap_deployments(strict=False))
        for ref, cap in self._flow_caps.items():
            if isinstance(cap, Agent):
                out[ref] = cap.deployment()
        return out

    def check(self) -> list[Diagnostic]:
        """Force full freeze validation without executing and return diagnostics."""
        return self._deploy(strict=False).diagnostics

    async def deploy(
        self,
        client: Any,
        *,
        session_id: str,
        input: Any = None,
        task_queue: str = "composable-agents",
        policy: Any = None,
        principal: Optional[dict[str, Any]] = None,
    ) -> Any:
        # Fail loud rather than diverge silently: the facade does not yet
        # auto-wire sub-capability child deployments into the Temporal worker's
        # registry, so a SUB decision would resolve via WorkerContext.subflows
        # (possibly stale/missing). Tool-only agents deploy normally.
        if self._flow_caps:
            raise NotImplementedError(
                "Agent.deploy() to Temporal does not yet auto-wire sub-capability "
                f"deployments into the worker (a documented seam). This agent has "
                f"sub-capabilities {sorted(self._flow_caps)}; their compiled child "
                "deployments are available via agent.sub_deployments() — register "
                "them on your worker (WorkerContext.subflows), then run the parent "
                "via agent.deployment().run(...). Tool-only agents deploy normally."
            )
        return await self._deploy().run(
            client,
            session_id=session_id,
            input=input,
            task_queue=task_queue,
            policy=policy,
            principal=principal,
        )
