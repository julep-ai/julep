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
from .execution.interpreter import InMemoryEnv, interpret
from .freeze import McpSnapshot, NativeToolSpec
from .flow import FlowLike
from .ir import JSONSchema, Node, canonical_json
from .kinds import Effect, EnforcementMode, Idempotency
from .projection import InMemoryProjection, ProjectionEmitter
from .validate import Diagnostic

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
    budget_usd: Optional[float],
    max_rounds: int,
    instructions: str,
) -> str:
    payload = canonical_json(
        {
            "budget_usd": budget_usd,
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

    def __init__(
        self,
        brain: str,
        tools: Sequence[Tool[Any, Any]] = (),
        *,
        name: Optional[str] = None,
        llm: Optional[Callable[[str, Any], Any]] = None,
        budget_usd: Optional[float] = None,
        max_rounds: int = 24,
        instructions: Optional[str] = None,
        mode: EnforcementMode | str = EnforcementMode.STRICT,
    ) -> None:
        """Create an agent facade.

        When ``name`` is omitted, the controller name is derived from the agent
        config. An explicit ``name`` is used unchanged and must be unique per
        distinct agent config in the current process.
        """
        tool_names = tuple(native_tool.name for native_tool in tools)
        system = instructions or ""
        if name is None:
            resolved_name = _derive_agent_name(
                model=brain,
                tool_names=tool_names,
                budget_usd=budget_usd,
                max_rounds=max_rounds,
                instructions=system,
            )
        else:
            resolved_name = name
        self._name = resolved_name
        self._brain_model = brain
        self._tools = tuple(tools)
        self._brain_fn = llm or default_local_brain
        self._budget = Budget(usd=budget_usd) if budget_usd is not None else None
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
            _has_tools=True,
        )
        self._deployment_cache: Optional[Deployment] = None
        self._eager_capability_checks()

    def to_ir(self) -> Node:
        return self._flow

    def _deploy(self) -> Deployment:
        if self._deployment_cache is None:
            self._deployment_cache = deploy(
                self._flow,
                self._snapshot,
                capabilities=self._capabilities,
                mode=self._mode,
            )
        return self._deployment_cache

    def _eager_capability_checks(self) -> None:
        names = [native_tool.name for native_tool in self._tools]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValidationError(
                [
                    Diagnostic(
                        "CAP_APP_TOOL_COLLISION",
                        self._flow.id,
                        f"duplicate capability name {name!r} among agent tools",
                    )
                    for name in duplicates
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

    async def arun(self, input: Any) -> dict[str, Any]:
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

        async def invoke_controller(payload: dict[str, Any]) -> Any:
            reply = self._brain_fn(self._brain_model, payload)
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
                    granted=self._granted,
                    contracts=contracts,
                )
            },
            max_calls=max_call_limits,
            mode=self._mode,
        )
        result = await interpret(deployment.flow, input, env)
        return cast(dict[str, Any], result.value)

    def run(self, input: Any) -> dict[str, Any]:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.arun(input))
        raise RuntimeError("Agent.run() cannot be called inside a running event loop; use await Agent.arun(...)")

    def deployment(self) -> Deployment:
        return self._deploy()

    def check(self) -> list[Diagnostic]:
        """Force full freeze validation without executing. In strict mode a blocking
        diagnostic raises ValidationError (via deploy); otherwise returns diagnostics."""
        return self._deploy().diagnostics

    async def deploy(
        self,
        client: Any,
        *,
        session_id: str,
        input: Any = None,
        task_queue: str = "composable-agents",
        policy: Any = None,
    ) -> Any:
        return await self._deploy().run(
            client,
            session_id=session_id,
            input=input,
            task_queue=task_queue,
            policy=policy,
        )
