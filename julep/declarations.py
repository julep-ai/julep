"""Portable, content-addressed runtime declarations for released pipelines."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from typing import Any, NoReturn, Optional

from .app import ApplicationDefinitionError, _reasoner_runtime_declaration
from .dotctx import Reasoner
from .ir import Node, SubContract, canonical_json
from .kinds import ContextScope, Op
from .registry import (
    DEFAULT_REGISTRY,
    Registry,
    RendererDeclaration,
    RendererDependency,
    RendererEntry,
)

_BLOB_SCHEMA_VERSION = 2
_SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")


class DeclarationError(RuntimeError):
    """A declarations blob is corrupt, inconsistent, or cannot be rebuilt."""


def _fail(message: str) -> NoReturn:
    raise DeclarationError(message)


def _object(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"{label} must be a JSON object")
    if not all(isinstance(key, str) for key in value):
        _fail(f"{label} keys must be strings")
    return value


def _string(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        _fail(f"{label} must be a string")
    return value


def _optional_string(value: Any, *, label: str) -> str | None:
    if value is None:
        return None
    return _string(value, label=label)


def _optional_int(value: Any, *, label: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        _fail(f"{label} must be an integer or null")
    return value


def _boolean(value: Any, *, label: str) -> bool:
    if not isinstance(value, bool):
        _fail(f"{label} must be a boolean")
    return value


def _string_mapping(value: Any, *, label: str) -> dict[str, str]:
    raw = _object(value, label=label)
    out: dict[str, str] = {}
    for key, item in raw.items():
        out[key] = _string(item, label=f"{label}.{key}")
    return out


def _renderer_source(
    name: str,
    registry: Registry,
) -> tuple[RendererEntry, RendererDeclaration]:
    source_registry = registry if name in registry.renderers else DEFAULT_REGISTRY
    entry = source_registry.renderers.get(name)
    if entry is None:
        raise ApplicationDefinitionError(f"reasoner references unknown renderer {name!r}")
    declaration = source_registry.renderer_declarations.get(name)
    if declaration is None:
        raise ApplicationDefinitionError(
            f"renderer {name!r} has no portable declaration; released pipelines require "
            "rich dotctx renderers or inline prompt strings"
        )
    return entry, declaration


def declarations_blob(
    reasoners: Iterable[Reasoner],
    *,
    registry: Registry,
    flow: Optional[Node] = None,
) -> bytes:
    """Serialize the reasoners and rich renderers needed by one pipeline."""

    reasoner_values: dict[str, Reasoner] = {}
    for reasoner in reasoners:
        existing = reasoner_values.get(reasoner.name)
        if existing is not None and existing != reasoner:
            raise ApplicationDefinitionError(
                f"conflicting reasoners named {reasoner.name!r} in declarations blob"
            )
        reasoner_values[reasoner.name] = reasoner

    renderer_names = {
        name
        for reasoner in reasoner_values.values()
        for name in (reasoner.system_render, reasoner.user_render)
        if name is not None
    }
    renderers: dict[str, dict[str, Any]] = {}
    for name in sorted(renderer_names):
        entry, declaration = _renderer_source(name, registry)
        renderers[name] = {
            "package": declaration.package,
            "role": declaration.role,
            "source": declaration.source,
            "baseDir": declaration.base_dir,
            "templates": dict(declaration.templates),
            "files": dict(declaration.files),
            "hashSource": declaration.hash_source,
            "sourceHash": entry.source_hash,
            "dependencies": [
                {
                    "kind": dependency.kind,
                    "ref": dependency.ref,
                    "rel": dependency.rel,
                    "content": dependency.content,
                    "exists": dependency.exists,
                }
                for dependency in declaration.dependencies
            ],
        }

    agents: dict[str, dict[str, Any]] = {}
    if flow is not None:
        for node in flow.walk():
            if node.op is not Op.APP or node.controller is None:
                continue
            encoded = node.to_json()
            config = {
                key: encoded[key]
                for key in (
                    "budget",
                    "maxRounds",
                    "ctx",
                    "summarizer",
                    "roundNote",
                    "nativeTools",
                    "requireToolCall",
                    "replySchema",
                    "outputRetries",
                )
                if key in encoded
            }
            spec: dict[str, Any] = {
                "config": config,
                "grantedTools": list(node.tools or ()),
                "toolAliases": dict(node.tool_aliases or {}),
                "toolDefs": list(node.tool_defs or ()),
                "grantedContracts": dict(node.tool_contracts or {}),
            }
            if node.subflows is not None:
                spec["grantedSubflows"] = list(node.subflows)
            if node.subflow_queues is not None:
                spec["subflowQueues"] = dict(node.subflow_queues)
            existing_agent = agents.get(node.controller)
            if existing_agent is not None and existing_agent != spec:
                raise ApplicationDefinitionError(
                    f"controller {node.controller!r} has conflicting APP declarations"
                )
            agents[node.controller] = spec

    payload = {
        "schemaVersion": _BLOB_SCHEMA_VERSION,
        "reasoners": {
            name: _reasoner_runtime_declaration(reasoner, registry=registry)
            for name, reasoner in sorted(reasoner_values.items())
        },
        "renderers": renderers,
        "agents": {name: agents[name] for name in sorted(agents)},
    }
    return canonical_json(payload).encode("utf-8")


def _renderer_dependency(name: str, index: int, raw: Any) -> RendererDependency:
    label = f"renderer {name!r} dependency {index}"
    value = _object(raw, label=label)
    kind = _string(value.get("kind"), label=f"{label} kind")
    if kind not in {"template", "import_yaml", "import_text"}:
        _fail(f"{label} has unsupported kind {kind!r}")
    return RendererDependency(
        kind=kind,
        ref=_string(value.get("ref"), label=f"{label} ref"),
        rel=_string(value.get("rel"), label=f"{label} rel"),
        content=_string(value.get("content"), label=f"{label} content"),
        exists=_boolean(value.get("exists"), label=f"{label} exists"),
    )


def _renderer_hash_source(
    source: str,
    dependencies: tuple[RendererDependency, ...],
) -> str:
    if not dependencies:
        return source
    chunks = [source, "\n\n# dotctx dependency bundle\n"]
    for dependency in dependencies:
        chunks.append(
            f"\n# {dependency.kind}: {dependency.rel}\n{dependency.content}"
        )
    return "".join(chunks)


def _rebuild_renderer(name: str, raw: Any) -> tuple[RendererEntry, RendererDeclaration]:
    from .dotctx_rich import _snapshot_key, _template_renderer

    value = _object(raw, label=f"renderer {name!r}")
    package = _string(value.get("package"), label=f"renderer {name!r} package")
    role = _string(value.get("role"), label=f"renderer {name!r} role")
    source = _string(value.get("source"), label=f"renderer {name!r} source")
    base_dir = _optional_string(value.get("baseDir"), label=f"renderer {name!r} baseDir")
    templates = _string_mapping(
        value.get("templates"), label=f"renderer {name!r} templates"
    )
    files = _string_mapping(value.get("files"), label=f"renderer {name!r} files")
    hash_source = _string(
        value.get("hashSource"), label=f"renderer {name!r} hashSource"
    )
    declared_hash = _string(
        value.get("sourceHash"), label=f"renderer {name!r} sourceHash"
    )
    dependencies_raw = value.get("dependencies")
    if not isinstance(dependencies_raw, list):
        _fail(f"renderer {name!r} dependencies must be a list")
    dependencies = tuple(
        _renderer_dependency(name, index, dependency)
        for index, dependency in enumerate(dependencies_raw)
    )
    expected_hash_source = _renderer_hash_source(source, dependencies)
    if hash_source != expected_hash_source:
        _fail(f"renderer {name!r} hash material does not match its reconstruction inputs")
    expected_templates = {
        dependency.ref: dependency.content
        for dependency in dependencies
        if dependency.kind == "template" and dependency.exists
    }
    expected_files = {
        _snapshot_key(dependency.ref, base_dir): dependency.content
        for dependency in dependencies
        if dependency.kind in {"import_yaml", "import_text"} and dependency.exists
    }
    if templates != expected_templates:
        _fail(f"renderer {name!r} templates do not match its captured dependencies")
    if files != expected_files:
        _fail(f"renderer {name!r} files do not match its captured dependencies")

    digest = hashlib.sha256(hash_source.encode("utf-8")).hexdigest()
    expected_name = f"dotctx/{package}/{role}@v{digest[:12]}"
    if name != expected_name:
        _fail(f"renderer {name!r} does not match its reconstructed content name")

    fn = _template_renderer(package, role, source, base_dir, templates, files)
    scratch = Registry()
    entry = scratch.register_renderer(name, fn, source=hash_source)
    if entry.source_hash != declared_hash:
        _fail(
            f"renderer {name!r} source hash mismatch: "
            f"declared {declared_hash}, rebuilt {entry.source_hash}"
        )
    declaration = RendererDeclaration(
        package=package,
        role=role,
        source=source,
        base_dir=base_dir,
        templates=templates,
        files=files,
        hash_source=hash_source,
        dependencies=dependencies,
    )
    return entry, declaration


def _reasoner_from_json(name: str, raw: Any) -> Reasoner:
    value = _object(raw, label=f"reasoner {name!r}")
    declared_name = _string(value.get("name"), label=f"reasoner {name!r} name")
    if declared_name != name:
        _fail(f"reasoner key {name!r} does not match declared name {declared_name!r}")

    tools_raw = value.get("tools")
    if not isinstance(tools_raw, list) or not all(isinstance(item, str) for item in tools_raw):
        _fail(f"reasoner {name!r} tools must be a list of strings")
    reply_raw = value.get("replySchema")
    reply = None if reply_raw is None else _object(reply_raw, label=f"reasoner {name!r} replySchema")
    sub_raw = value.get("subContract")
    sub_contract = (
        None
        if sub_raw is None
        else SubContract.from_json(_object(sub_raw, label=f"reasoner {name!r} subContract"))
    )
    temperature_raw = value.get("temperature")
    if temperature_raw is not None and (
        not isinstance(temperature_raw, (int, float)) or isinstance(temperature_raw, bool)
    ):
        _fail(f"reasoner {name!r} temperature must be numeric or null")
    is_agent = value.get("isAgent")
    require_tool_call = value.get("requireToolCall")
    if not isinstance(is_agent, bool):
        _fail(f"reasoner {name!r} isAgent must be a boolean")
    if not isinstance(require_tool_call, bool):
        _fail(f"reasoner {name!r} requireToolCall must be a boolean")
    output_retries = value.get("outputRetries")
    if not isinstance(output_retries, int) or isinstance(output_retries, bool):
        _fail(f"reasoner {name!r} outputRetries must be an integer")

    return Reasoner(
        name=declared_name,
        model=_string(value.get("model"), label=f"reasoner {name!r} model"),
        system=_string(value.get("system"), label=f"reasoner {name!r} system"),
        reply=reply,
        tools=tools_raw,
        temperature=float(temperature_raw) if temperature_raw is not None else None,
        max_rounds=_optional_int(value.get("maxRounds"), label=f"reasoner {name!r} maxRounds"),
        is_agent=is_agent,
        sub_contract=sub_contract,
        context_scope=ContextScope(
            _string(value.get("contextScope"), label=f"reasoner {name!r} contextScope")
        ),
        system_render=_optional_string(
            value.get("systemRender"), label=f"reasoner {name!r} systemRender"
        ),
        user_render=_optional_string(
            value.get("userRender"), label=f"reasoner {name!r} userRender"
        ),
        max_tokens=_optional_int(value.get("maxTokens"), label=f"reasoner {name!r} maxTokens"),
        reasoning_effort=_optional_string(
            value.get("reasoningEffort"), label=f"reasoner {name!r} reasoningEffort"
        ),
        output_retries=output_retries,
        require_tool_call=require_tool_call,
        response_format=_optional_string(
            value.get("responseFormat"), label=f"reasoner {name!r} responseFormat"
        ),
        prompt_cache=_optional_string(
            value.get("promptCache"), label=f"reasoner {name!r} promptCache"
        ),
    )


def _target_registries(registry: Registry, *, release_scoped: bool) -> list[Registry]:
    if release_scoped:
        return [registry]
    targets = [DEFAULT_REGISTRY]
    if registry is not DEFAULT_REGISTRY:
        targets.append(registry)
    return targets


def _agent_spec_from_json(name: str, raw: Any) -> dict[str, Any]:
    value = _object(raw, label=f"agent {name!r}")
    config = _object(value.get("config"), label=f"agent {name!r} config")
    grants = value.get("grantedTools")
    if not isinstance(grants, list) or not all(isinstance(item, str) for item in grants):
        _fail(f"agent {name!r} grantedTools must be a list of strings")
    aliases = _string_mapping(
        value.get("toolAliases"), label=f"agent {name!r} toolAliases"
    )
    if set(aliases) != set(grants):
        _fail(f"agent {name!r} toolAliases must exactly match grantedTools")
    tool_defs = value.get("toolDefs")
    if not isinstance(tool_defs, list) or not all(isinstance(item, dict) for item in tool_defs):
        _fail(f"agent {name!r} toolDefs must be a list of JSON objects")
    contracts = _object(
        value.get("grantedContracts"), label=f"agent {name!r} grantedContracts"
    )
    if set(contracts) != set(grants):
        _fail(f"agent {name!r} grantedContracts must exactly match grantedTools")
    tool_def_names: list[str] = []
    for index, tool_def in enumerate(tool_defs):
        function = _object(
            tool_def.get("function"), label=f"agent {name!r} toolDefs[{index}].function"
        )
        tool_def_names.append(
            _string(function.get("name"), label=f"agent {name!r} toolDefs[{index}] name")
        )
        _object(
            function.get("parameters"),
            label=f"agent {name!r} toolDefs[{index}] parameters",
        )
    if set(tool_def_names) != set(grants) or len(tool_def_names) != len(grants):
        _fail(f"agent {name!r} toolDefs must define every granted tool exactly once")

    out: dict[str, Any] = {
        "config": config,
        "grantedTools": list(grants),
        "toolAliases": aliases,
        "toolDefs": list(tool_defs),
        "grantedContracts": contracts,
    }
    if "grantedSubflows" in value:
        subflows = value["grantedSubflows"]
        if not isinstance(subflows, list) or not all(isinstance(item, str) for item in subflows):
            _fail(f"agent {name!r} grantedSubflows must be a list of strings")
        out["grantedSubflows"] = list(subflows)
    if "subflowQueues" in value:
        out["subflowQueues"] = _string_mapping(
            value["subflowQueues"], label=f"agent {name!r} subflowQueues"
        )
    return out


def load_declarations(
    blob: bytes,
    *,
    expected_hash: str,
    registry: Registry,
    release_scoped: bool = False,
) -> None:
    """Verify, rebuild, cross-check, and register a declarations blob."""

    if _SHA256_REF.fullmatch(expected_hash) is None:
        _fail("expected declarations hash must be sha256:<64 lowercase hex>")
    actual_hash = "sha256:" + hashlib.sha256(blob).hexdigest()
    if actual_hash != expected_hash:
        _fail(
            f"declarations blob hash mismatch: expected {expected_hash}, got {actual_hash}"
        )
    try:
        decoded = json.loads(blob)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeclarationError("declarations blob is not valid JSON") from exc
    payload = _object(decoded, label="declarations blob")
    schema_version = payload.get("schemaVersion")
    if type(schema_version) is not int or schema_version != _BLOB_SCHEMA_VERSION:
        _fail(
            "unsupported declarations blob schema version "
            f"{schema_version!r}; expected {_BLOB_SCHEMA_VERSION}"
        )

    renderer_values = _object(payload.get("renderers"), label="declarations renderers")
    rebuilt_renderers: dict[str, RendererEntry] = {}
    renderer_declarations: dict[str, RendererDeclaration] = {}
    for name, raw in renderer_values.items():
        entry, declaration = _rebuild_renderer(name, raw)
        rebuilt_renderers[name] = entry
        renderer_declarations[name] = declaration

    reasoner_values = _object(payload.get("reasoners"), label="declarations reasoners")
    rebuilt_reasoners = {
        name: _reasoner_from_json(name, raw) for name, raw in reasoner_values.items()
    }
    for name, reasoner in rebuilt_reasoners.items():
        raw = _object(reasoner_values[name], label=f"reasoner {name!r}")
        declared_hashes = _string_mapping(
            raw.get("rendererSourceHashes"),
            label=f"reasoner {name!r} rendererSourceHashes",
        )
        referenced = {
            renderer_name
            for renderer_name in (reasoner.system_render, reasoner.user_render)
            if renderer_name is not None
        }
        if set(declared_hashes) != referenced:
            _fail(f"reasoner {name!r} renderer declarations do not match its configuration")
        for renderer_name, declared_hash in declared_hashes.items():
            rebuilt_renderer = rebuilt_renderers.get(renderer_name)
            if rebuilt_renderer is None or rebuilt_renderer.source_hash != declared_hash:
                _fail(
                    f"reasoner {name!r} renderer {renderer_name!r} hash does not "
                    "match the rebuilt declaration"
                )

    agent_values = _object(payload.get("agents"), label="declarations agents")
    rebuilt_agents = {
        name: _agent_spec_from_json(name, raw) for name, raw in agent_values.items()
    }

    targets = _target_registries(registry, release_scoped=release_scoped)
    for target in targets:
        for reasoner in rebuilt_reasoners.values():
            existing_reasoner = target.reasoners.get(reasoner.name)
            if existing_reasoner is not None and existing_reasoner != reasoner:
                raise ApplicationDefinitionError(
                    f"reasoner {reasoner.name!r} conflicts with the verified "
                    "application declaration"
                )
        for name, entry in rebuilt_renderers.items():
            existing_renderer = target.renderers.get(name)
            if (
                existing_renderer is not None
                and existing_renderer.source_hash != entry.source_hash
            ):
                raise ApplicationDefinitionError(
                    f"renderer {name!r} conflicts with the verified application declaration"
                )
        for name, spec in rebuilt_agents.items():
            existing_agent = target.agent_specs.get(name)
            if existing_agent is not None and existing_agent != spec:
                raise ApplicationDefinitionError(
                    f"agent {name!r} conflicts with the verified application declaration"
                )

    for target in targets:
        for reasoner in rebuilt_reasoners.values():
            target.register_reasoner(reasoner)
        for name, entry in rebuilt_renderers.items():
            target.renderers[name] = entry
            target.renderer_declarations[name] = renderer_declarations[name]
        target.agent_specs.update(rebuilt_agents)

    # Renderer names are content-addressed, so sharing them process-wide is
    # safe even when reasoner names are release-scoped. The prompt adapter's
    # historical renderer lookup remains global; conflicting content under the
    # same renderer name was rejected above.
    if release_scoped and registry is not DEFAULT_REGISTRY:
        for name, entry in rebuilt_renderers.items():
            existing_renderer = DEFAULT_REGISTRY.renderers.get(name)
            if (
                existing_renderer is not None
                and existing_renderer.source_hash != entry.source_hash
            ):
                raise ApplicationDefinitionError(
                    f"renderer {name!r} conflicts with a loaded release declaration"
                )
            DEFAULT_REGISTRY.renderers[name] = entry
            DEFAULT_REGISTRY.renderer_declarations[name] = renderer_declarations[name]


__all__ = ["DeclarationError", "declarations_blob", "load_declarations"]
