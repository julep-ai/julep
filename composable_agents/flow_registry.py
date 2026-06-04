from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .ir import Node, canonical_json
from .registry import DEFAULT_REGISTRY, Registry
from .transforms import normalize_ids


class FlowRegistryError(ValueError):
    """Raised when a flow ref is ambiguous or collides with another name."""


@runtime_checkable
class _Lowerable(Protocol):
    def to_ir(self) -> Node: ...


@dataclass(frozen=True)
class FlowSpec:
    ref: str
    node: Node


def _canonical_ir(node: Node) -> str:
    return canonical_json(normalize_ids(Node.from_json(node.to_json())).to_json())


class FlowRegistry:
    """Durable named-flow registry (authoring layer).

    One name space shared with brains/tools: a flow ref may not collide with a
    registered brain name or a tool name carried by a registered brain (design
    §6 collision policy).
    """

    def __init__(self, brain_registry: Registry = DEFAULT_REGISTRY) -> None:
        self._flows: dict[str, FlowSpec] = {}
        self._brain_registry = brain_registry

    def register_flow(
        self,
        ref: str,
        flow_or_node: Node | _Lowerable,
        *,
        replace: bool = False,
    ) -> FlowSpec:
        node = flow_or_node if isinstance(flow_or_node, Node) else flow_or_node.to_ir()
        spec = FlowSpec(ref=ref, node=node)
        existing = self._flows.get(ref)
        if existing is not None and not replace:
            # Idempotent re-register of the same flow is fine; a different one collides.
            if _canonical_ir(existing.node) != _canonical_ir(node):
                raise FlowRegistryError(
                    f"flow ref {ref!r} already registered with a different flow"
                )
            return existing
        self._reject_cross_namespace_collision(ref)
        self._flows[ref] = spec
        return spec

    def get_flow(self, ref: str) -> FlowSpec:
        try:
            return self._flows[ref]
        except KeyError as exc:
            raise FlowRegistryError(
                f"unknown flow ref {ref!r}; register it with .named({ref!r})"
            ) from exc

    def has_flow(self, ref: str) -> bool:
        return ref in self._flows

    def _reject_cross_namespace_collision(self, ref: str) -> None:
        brains = self._brain_registry.brains
        if ref in brains:
            raise FlowRegistryError(f"flow ref {ref!r} collides with a registered brain name")
        for brain in brains.values():
            if ref in tuple(getattr(brain, "tools", ()) or ()):
                raise FlowRegistryError(f"flow ref {ref!r} collides with a registered tool name")


DEFAULT_FLOW_REGISTRY = FlowRegistry()


def register_flow(
    ref: str,
    flow_or_node: Node | _Lowerable,
    *,
    replace: bool = False,
) -> FlowSpec:
    return DEFAULT_FLOW_REGISTRY.register_flow(ref, flow_or_node, replace=replace)


def get_flow(ref: str) -> FlowSpec:
    return DEFAULT_FLOW_REGISTRY.get_flow(ref)
