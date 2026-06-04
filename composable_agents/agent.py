"""Small facade helpers for native Python-callable tools."""

from __future__ import annotations

import inspect
import types
from collections.abc import Mapping as AbcMapping
from collections.abc import Sequence as AbcSequence
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence, Union, get_args, get_origin, get_type_hints, overload

from .contracts import ToolContract
from .freeze import McpSnapshot, NativeToolSpec
from .ir import JSONSchema
from .kinds import Effect, Idempotency

_OBJECT_SCHEMA: JSONSchema = {"type": "object"}
_ALLOWED_EFFECTS = ("read", "write", "external", "dangerous")
_NONE_TYPE = type(None)


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


def _schema_from_hints(fn: Callable[..., Any]) -> tuple[JSONSchema, JSONSchema]:
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
    if positional:
        parameter = positional[0]
        input_type = hints.get(parameter.name, parameter.annotation)
    else:
        input_type = inspect.Signature.empty

    output_type = hints.get("return", signature.return_annotation)
    return python_type_to_schema(input_type), python_type_to_schema(output_type)


@dataclass(frozen=True)
class Tool:
    name: str
    fn: Callable[..., Any]
    contract: ToolContract
    input_schema: JSONSchema
    output_schema: JSONSchema

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)

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
) -> Tool:
    input_schema, output_schema = _schema_from_hints(fn)
    return Tool(
        name=name or fn.__name__,
        fn=fn,
        contract=ToolContract(
            effect=effect,
            idempotency=Idempotency.NATIVE if idempotent else Idempotency.NONE,
        ),
        input_schema=input_schema,
        output_schema=output_schema,
    )


@overload
def tool(fn: Callable[..., Any], /) -> Tool:
    ...


@overload
def tool(
    fn: None = None,
    /,
    *,
    effect: str = "write",
    idempotent: bool = False,
    name: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Tool]:
    ...


def tool(
    fn: Optional[Callable[..., Any]] = None,
    /,
    *,
    effect: str = "write",
    idempotent: bool = False,
    name: Optional[str] = None,
) -> Tool | Callable[[Callable[..., Any]], Tool]:
    mapped_effect = _effect_from_string(effect)

    def decorate(inner: Callable[..., Any]) -> Tool:
        return _build_tool(inner, effect=mapped_effect, idempotent=idempotent, name=name)

    if fn is not None:
        return decorate(fn)
    return decorate


def snapshot_from_tools(tools: Sequence[Tool]) -> McpSnapshot:
    return McpSnapshot(native={native_tool.name: native_tool.native_spec for native_tool in tools})
