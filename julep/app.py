"""Explicit application and pipeline deployment objects.

An :class:`Application` is the unit deployed by the application-level CLI.  It
contains ordinary Python objects and deliberately does not participate in the
decorator/AST discovery path used by the legacy flow CLI.
"""

from __future__ import annotations

import hashlib
import importlib
import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Generic, Mapping, Optional, Sequence, TypeVar

from .capabilities import CapabilityManifest
from .deploy import Deployment, _referenced_reasoners, deploy
from .dotctx import Reasoner
from .freeze import McpSnapshot
from .ir import Node, canonical_json
from .registry import DEFAULT_REGISTRY, Registry

if TYPE_CHECKING:
    from .agent import Tool
    from .typed import FlowLike

Input = TypeVar("Input")
Output = TypeVar("Output")
_KUBERNETES_LABEL_VALUE = re.compile(
    r"^[a-z0-9](?:[-a-z0-9_.]{0,61}[a-z0-9])?$"
)


class ApplicationDefinitionError(ValueError):
    """An application declaration is ambiguous or cannot be compiled."""


@dataclass(frozen=True)
class PipelineSpec(Generic[Input, Output]):
    """One typed pipeline in an application.

    ``snapshot`` and ``tools`` are alternative compile-time schema sources.
    They are explicit values rather than discovered globals. ``snapshot_source``
    receives the selected deployment environment as a read-only string mapping.
    A caller may also provide a fresher per-pipeline snapshot to
    :meth:`Application.compile`, which is how ``julep plan`` compares a declared
    MCP schema with the live one.
    """

    name: str
    flow: Node | FlowLike[Input, Output]
    reasoners: Sequence[str | Reasoner] = ()
    capabilities: CapabilityManifest = field(default_factory=CapabilityManifest)
    lane: str = "default"
    eval_packages: Sequence[str] = ()
    snapshot: Optional[McpSnapshot] = None
    snapshot_source: Optional[Callable[[Mapping[str, str]], McpSnapshot]] = None
    tools: Sequence[Tool[Any, Any]] = ()

    def __post_init__(self) -> None:
        if not self.name or self.name.strip() != self.name:
            raise ApplicationDefinitionError("pipeline name must be a non-empty trimmed string")
        if not self.lane or self.lane.strip() != self.lane:
            raise ApplicationDefinitionError(
                f"pipeline {self.name!r} lane must be a non-empty trimmed string"
            )
        if _KUBERNETES_LABEL_VALUE.fullmatch(self.lane) is None:
            raise ApplicationDefinitionError(
                f"pipeline {self.name!r} lane must be a lowercase Kubernetes "
                "label value of at most 63 characters"
            )
        reasoners = tuple(self.reasoners)
        eval_packages = tuple(self.eval_packages)
        tools = tuple(self.tools)
        reasoner_names = [r.name if isinstance(r, Reasoner) else r for r in reasoners]
        if len(reasoner_names) != len(set(reasoner_names)):
            raise ApplicationDefinitionError(
                f"pipeline {self.name!r} declares a reasoner more than once"
            )
        flow = self.flow if isinstance(self.flow, Node) else self.flow.to_ir()
        undeclared = sorted(set(_referenced_reasoners(flow)) - set(reasoner_names))
        if undeclared:
            raise ApplicationDefinitionError(
                f"pipeline {self.name!r} flow references undeclared reasoners: "
                + ", ".join(undeclared)
            )
        if any(not package or package.strip() != package for package in eval_packages):
            raise ApplicationDefinitionError(
                f"pipeline {self.name!r} eval package names must be non-empty and trimmed"
            )
        if len(eval_packages) != len(set(eval_packages)):
            raise ApplicationDefinitionError(
                f"pipeline {self.name!r} declares an eval package more than once"
            )
        if self.snapshot is not None and tools:
            raise ApplicationDefinitionError(
                f"pipeline {self.name!r} must declare either snapshot or tools, not both"
            )
        if self.snapshot_source is not None and tools:
            raise ApplicationDefinitionError(
                f"pipeline {self.name!r} cannot use a live MCP snapshot source with native tools"
            )
        if self.snapshot_source is not None and not callable(self.snapshot_source):
            raise ApplicationDefinitionError(
                f"pipeline {self.name!r} snapshot_source must be callable"
            )
        object.__setattr__(self, "reasoners", reasoners)
        object.__setattr__(self, "eval_packages", eval_packages)
        object.__setattr__(self, "tools", tools)

    @property
    def reasoner_names(self) -> tuple[str, ...]:
        return tuple(r.name if isinstance(r, Reasoner) else r for r in self.reasoners)

    def to_declaration_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "lane": self.lane,
            "reasoners": sorted(self.reasoner_names),
            "capabilities": self.capabilities.to_json(),
            "evalPackages": list(self.eval_packages),
        }


@dataclass(frozen=True)
class CompiledPipeline(Generic[Input, Output]):
    spec: PipelineSpec[Input, Output]
    deployment: Deployment
    declared_schema_hash: str
    compiled_schema_hash: str
    runtime_declarations_blob: Optional[bytes] = field(
        default=None,
        compare=False,
        repr=False,
    )

    @property
    def mcp_schema_drift(self) -> bool:
        return self.declared_schema_hash != self.compiled_schema_hash

    def to_json(self) -> dict[str, Any]:
        data = self.spec.to_declaration_json()
        data.update(
            {
                "artifactHash": self.deployment.artifact_hash,
                "declaredMcpSchemaHash": self.declared_schema_hash,
                "compiledMcpSchemaHash": self.compiled_schema_hash,
            }
        )
        return data


@dataclass(frozen=True)
class CompiledApplication:
    name: str
    pipelines: tuple[CompiledPipeline[Any, Any], ...]
    runtime_declarations_hash: str

    @cached_property
    def artifact_components(self) -> dict[str, Any]:
        return {
            "application": self.name,
            "runtimeDeclarationsHash": self.runtime_declarations_hash,
            "pipelines": [pipeline.to_json() for pipeline in self.pipelines],
        }

    @cached_property
    def artifact_hash(self) -> str:
        digest = hashlib.sha256(
            canonical_json(self.artifact_components).encode("utf-8")
        ).hexdigest()
        return f"sha256:{digest}"

    @property
    def lanes(self) -> dict[str, tuple[str, ...]]:
        lanes: dict[str, list[str]] = {}
        for pipeline in self.pipelines:
            lanes.setdefault(pipeline.spec.lane, []).append(pipeline.spec.name)
        return {
            lane: tuple(sorted(names))
            for lane, names in sorted(lanes.items())
        }


@dataclass(frozen=True)
class Application:
    """A deterministic collection of named pipelines."""

    name: str
    pipelines: Sequence[PipelineSpec[Any, Any]]

    def __post_init__(self) -> None:
        if not self.name or self.name.strip() != self.name:
            raise ApplicationDefinitionError(
                "application name must be a non-empty trimmed string"
            )
        if _KUBERNETES_LABEL_VALUE.fullmatch(self.name) is None:
            raise ApplicationDefinitionError(
                "application name must be a lowercase Kubernetes label value "
                "of at most 63 characters"
            )
        pipelines = tuple(self.pipelines)
        if not pipelines:
            raise ApplicationDefinitionError(
                f"application {self.name!r} must declare at least one pipeline"
            )
        names = [pipeline.name for pipeline in pipelines]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ApplicationDefinitionError(
                f"application {self.name!r} has duplicate pipeline names: "
                + ", ".join(duplicates)
            )
        declared_reasoners: dict[str, Reasoner] = {}
        for pipeline in pipelines:
            for reasoner in pipeline.reasoners:
                if not isinstance(reasoner, Reasoner):
                    continue
                existing = declared_reasoners.get(reasoner.name)
                if existing is not None and existing != reasoner:
                    raise ApplicationDefinitionError(
                        f"application {self.name!r} declares conflicting reasoners "
                        f"named {reasoner.name!r} across pipelines"
                    )
                declared_reasoners[reasoner.name] = reasoner
        object.__setattr__(self, "pipelines", pipelines)

    @cached_property
    def runtime_declarations_hash(self) -> str:
        """Hash declarations that an application worker must load at startup.

        The import target is pinned separately in the immutable release deployment
        config. This hash lets a worker reject an environment-dependent or otherwise
        changed declaration from that module without recompiling against live MCP
        schemas. Renderer source hashes are included because a named renderer changes
        the prompt sent by an otherwise identical :class:`Reasoner`.
        """

        return self._runtime_declarations_hash()

    def _runtime_declarations_hash(
        self,
        registry: Optional[Registry] = None,
    ) -> str:
        declarations = {
            name: _reasoner_runtime_declaration(reasoner, registry=registry)
            for name, reasoner in self._resolved_reasoners(registry).items()
        }
        digest = hashlib.sha256(
            canonical_json(declarations).encode("utf-8")
        ).hexdigest()
        return f"sha256:{digest}"

    def register_runtime_declarations(
        self,
        *,
        expected_hash: str,
        registry: Optional[Registry] = None,
    ) -> None:
        """Verify and register application-owned declarations in this process."""

        reasoners = self._resolved_reasoners(registry)
        actual_hash = self._runtime_declarations_hash(registry)
        if actual_hash != expected_hash:
            raise ApplicationDefinitionError(
                "worker application runtime declarations do not match the immutable "
                f"release: expected {expected_hash}, loaded {actual_hash}"
            )
        renderer_names = {
            name
            for reasoner in reasoners.values()
            for name in (reasoner.system_render, reasoner.user_render)
            if name is not None
        }
        renderer_sources = {
            name: _resolve_renderer(name, registry)
            for name in renderer_names
        }
        renderer_declarations = {
            name: declaration
            for name in renderer_names
            if (
                declaration := (
                    registry.renderer_declarations.get(name)
                    if registry is not None and name in registry.renderers
                    else DEFAULT_REGISTRY.renderer_declarations.get(name)
                )
            )
            is not None
        }
        target_registries = [DEFAULT_REGISTRY]
        if registry is not None and registry is not DEFAULT_REGISTRY:
            target_registries.append(registry)
        for target_registry in target_registries:
            for reasoner in reasoners.values():
                existing = target_registry.reasoners.get(reasoner.name)
                if existing is not None and existing != reasoner:
                    raise ApplicationDefinitionError(
                        f"reasoner {reasoner.name!r} conflicts with the verified "
                        "application declaration"
                    )
            for name, source in renderer_sources.items():
                existing_renderer = target_registry.renderers.get(name)
                if (
                    existing_renderer is not None
                    and existing_renderer.source_hash != source.source_hash
                ):
                    raise ApplicationDefinitionError(
                        f"renderer {name!r} conflicts with the verified "
                        "application declaration"
                    )

        for target_registry in target_registries:
            for reasoner in reasoners.values():
                target_registry.register_reasoner(reasoner)
            for name, source in renderer_sources.items():
                target_registry.renderers[name] = source
                declaration = renderer_declarations.get(name)
                if declaration is not None:
                    target_registry.renderer_declarations[name] = declaration

    def _resolved_reasoners(
        self,
        registry: Optional[Registry] = None,
    ) -> dict[str, Reasoner]:
        inline: dict[str, Reasoner] = {}
        for pipeline in self.pipelines:
            for reasoner in pipeline.reasoners:
                if isinstance(reasoner, Reasoner):
                    existing = inline.get(reasoner.name)
                    if existing is not None and existing != reasoner:
                        raise ApplicationDefinitionError(
                            f"application {self.name!r} declares conflicting reasoners "
                            f"named {reasoner.name!r} across pipelines"
                        )
                    inline[reasoner.name] = reasoner

        resolved = dict(inline)
        for pipeline in self.pipelines:
            for declaration in pipeline.reasoners:
                name = declaration.name if isinstance(declaration, Reasoner) else declaration
                if name in resolved:
                    continue
                resolved_reasoner: Optional[Reasoner] = None
                if registry is not None:
                    resolved_reasoner = registry.reasoners.get(name)
                if resolved_reasoner is None:
                    resolved_reasoner = DEFAULT_REGISTRY.reasoners.get(name)
                if resolved_reasoner is None:
                    raise ApplicationDefinitionError(
                        f"pipeline {pipeline.name!r} declares unknown reasoner {name!r}"
                    )
                resolved[name] = resolved_reasoner
        return resolved

    def compile(
        self,
        snapshots: Optional[Mapping[str, McpSnapshot]] = None,
        *,
        strict: bool = True,
    ) -> CompiledApplication:
        """Compile all pipelines in stable name order.

        ``snapshots`` is an optional live-schema override keyed by pipeline.  A
        mismatch is retained on :class:`CompiledPipeline` for plan output; the
        live snapshot is the one actually frozen into the artifact.
        """

        snapshots = snapshots or {}
        unknown = sorted(set(snapshots) - {pipeline.name for pipeline in self.pipelines})
        if unknown:
            raise ApplicationDefinitionError(
                "snapshot overrides reference unknown pipelines: " + ", ".join(unknown)
            )

        runtime_declarations_hash = self.runtime_declarations_hash
        self.register_runtime_declarations(
            expected_hash=runtime_declarations_hash,
        )
        resolved_reasoners = self._resolved_reasoners()
        from .declarations import declarations_blob

        compiled: list[CompiledPipeline[Any, Any]] = []
        for spec in sorted(self.pipelines, key=lambda pipeline: pipeline.name):
            declared_snapshot = spec.snapshot or McpSnapshot(servers={})
            compile_snapshot = snapshots.get(spec.name, declared_snapshot)
            if spec.tools:
                if spec.name in snapshots:
                    raise ApplicationDefinitionError(
                        f"pipeline {spec.name!r} uses native tools and cannot take an MCP "
                        "snapshot override"
                    )
                deployment = deploy(
                    spec.flow,
                    tools=spec.tools,
                    capabilities=spec.capabilities,
                    strict=strict,
                    queue=spec.lane,
                )
            else:
                deployment = deploy(
                    spec.flow,
                    snapshot=compile_snapshot,
                    capabilities=spec.capabilities,
                    strict=strict,
                    queue=spec.lane,
                )
            compiled.append(
                CompiledPipeline(
                    spec=spec,
                    deployment=deployment,
                    declared_schema_hash=_snapshot_hash(declared_snapshot),
                    compiled_schema_hash=_snapshot_hash(compile_snapshot),
                    runtime_declarations_blob=(
                        declarations_blob(
                            (resolved_reasoners[name] for name in spec.reasoner_names),
                            registry=DEFAULT_REGISTRY,
                        )
                        if spec.reasoner_names
                        else None
                    ),
                )
            )
        return CompiledApplication(
            name=self.name,
            pipelines=tuple(compiled),
            runtime_declarations_hash=runtime_declarations_hash,
        )

    def compile_live(
        self,
        *,
        env_vars: Optional[Mapping[str, str]] = None,
        strict: bool = True,
    ) -> CompiledApplication:
        """Compile against each pipeline's explicit live MCP snapshot source.

        Pipelines without a source retain their declared static snapshot. This
        keeps ordinary library compilation deterministic while giving
        application-level ``plan``/``apply`` a concrete tools/list refresh seam.
        """

        snapshot_environment = MappingProxyType(dict(env_vars or {}))
        snapshots: dict[str, McpSnapshot] = {}
        for spec in self.pipelines:
            if spec.snapshot_source is None:
                continue
            snapshot = spec.snapshot_source(snapshot_environment)
            if not isinstance(snapshot, McpSnapshot):
                raise ApplicationDefinitionError(
                    f"pipeline {spec.name!r} snapshot_source returned "
                    f"{type(snapshot).__name__}, expected McpSnapshot"
                )
            snapshots[spec.name] = snapshot
        return self.compile(snapshots, strict=strict)

    def run_evals(
        self,
        llm_caller: Callable[..., Any],
        *,
        root: str | Path = ".",
        env_vars: Optional[Mapping[str, str]] = None,
    ) -> dict[str, tuple[Any, ...]]:
        """Run declared eval packages through the supplied production caller."""

        from .cli.evalrun import run_eval_sync

        base = Path(root)
        return {
            spec.name: tuple(
                run_eval_sync(
                    str(base / package),
                    env_vars=env_vars,
                    llm_caller=llm_caller,
                )
                for package in spec.eval_packages
            )
            for spec in sorted(self.pipelines, key=lambda pipeline: pipeline.name)
        }


def _snapshot_hash(snapshot: McpSnapshot) -> str:
    payload = {
        "servers": {
            name: {
                "server": server.server,
                "version": server.version,
                "tools": {
                    tool_name: {
                        "inputSchema": tool.input_schema,
                        "outputSchema": tool.output_schema,
                        "annotations": tool.annotations.to_json(),
                    }
                    for tool_name, tool in sorted(server.tools.items())
                },
            }
            for name, server in sorted(snapshot.servers.items())
        },
        "native": {
            name: {
                "inputSchema": tool.input_schema,
                "outputSchema": tool.output_schema,
                "contract": tool.contract.to_json(),
            }
            for name, tool in sorted(snapshot.native.items())
        },
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _resolve_renderer(name: str, registry: Optional[Registry] = None) -> Any:
    renderer = registry.renderers.get(name) if registry is not None else None
    if renderer is None:
        renderer = DEFAULT_REGISTRY.renderers.get(name)
    if renderer is None:
        raise ApplicationDefinitionError(
            f"reasoner references unknown renderer {name!r}"
        )
    return renderer


def _reasoner_runtime_declaration(
    reasoner: Reasoner,
    *,
    registry: Optional[Registry] = None,
) -> dict[str, Any]:
    renderer_hashes: dict[str, str] = {}
    for renderer_name in (reasoner.system_render, reasoner.user_render):
        if renderer_name is None:
            continue
        renderer_hashes[renderer_name] = _resolve_renderer(
            renderer_name,
            registry,
        ).source_hash
    return {
        "name": reasoner.name,
        "model": reasoner.model,
        "system": reasoner.system,
        "replySchema": reasoner.reply_schema,
        "tools": list(reasoner.tools),
        "temperature": reasoner.temperature,
        "maxRounds": reasoner.max_rounds,
        "isAgent": reasoner.is_agent,
        "subContract": (
            reasoner.sub_contract.to_json()
            if reasoner.sub_contract is not None
            else None
        ),
        "contextScope": reasoner.context_scope.value,
        "systemRender": reasoner.system_render,
        "userRender": reasoner.user_render,
        "maxTokens": reasoner.max_tokens,
        "reasoningEffort": reasoner.reasoning_effort,
        "outputRetries": reasoner.output_retries,
        "requireToolCall": reasoner.require_tool_call,
        "responseFormat": reasoner.response_format,
        "promptCache": reasoner.prompt_cache,
        "rendererSourceHashes": renderer_hashes,
    }


def load_application_spec(spec: str) -> Application:
    """Resolve an explicit ``module:attribute`` application import target."""

    module_name, separator, attr_path = spec.partition(":")
    if not separator or not module_name or not attr_path:
        raise ValueError("application must use the explicit 'module:attribute' form")
    try:
        resolved: Any = importlib.import_module(module_name)
    except ImportError as exc:
        raise ValueError(f"cannot import application module {module_name!r}: {exc}") from exc
    for part in attr_path.split("."):
        try:
            resolved = getattr(resolved, part)
        except AttributeError as exc:
            raise ValueError(
                f"application {spec!r}: module {module_name!r} has no attribute "
                f"{attr_path!r}"
            ) from exc
    if not isinstance(resolved, Application):
        raise TypeError(
            f"configured application {spec!r} resolved to "
            f"{type(resolved).__name__}, expected julep.app.Application"
        )
    return resolved


__all__ = [
    "Application",
    "ApplicationDefinitionError",
    "CompiledApplication",
    "CompiledPipeline",
    "PipelineSpec",
    "load_application_spec",
]
