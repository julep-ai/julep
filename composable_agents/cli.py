"""Command-line inspection tools for Composable Agents artifacts."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional, Sequence, TextIO

from .capabilities import CapabilityManifest, check_approval_gates
from .contracts import McpAnnotations, ToolContract, ToolManifest, manifest_from_json
from .deploy import Deployment, deploy, snapshot_from_listings
from .derived import check_race_admission
from .diagnostics import explain
from .errors import ComposableAgentsError
from .execution.interpreter import InMemoryEnv, interpret
from .freeze import McpServerSnapshot, McpSnapshot, McpToolSpec, NativeToolSpec
from .ir import CallStep, Node, SubStep, toolref_key
from .kinds import Op
from .projection import EventType, InMemoryProjection, ProjectionEmitter
from .shapes import closed_shape, surface_shape
from .validate import Diagnostic, blocking, validate


def main(argv: Optional[Sequence[str]] = None, *, stdout: TextIO | None = None) -> int:
    """Run the CLI and return a process exit code."""
    out = stdout or sys.stdout
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args, out)
    except (ComposableAgentsError, KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="composable-agents",
        description="Validate, freeze, inspect, locally run, and graph Composable Agents JSON IR.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate_p = sub.add_parser("validate", help="validate a flow JSON artifact")
    validate_p.add_argument("flow_json")
    validate_p.add_argument("--manifest")
    validate_p.set_defaults(func=_cmd_validate)

    freeze_p = sub.add_parser("freeze", help="freeze a flow against a snapshot JSON artifact")
    freeze_p.add_argument("flow_json")
    freeze_p.add_argument("snapshot_json")
    freeze_p.add_argument("--caps")
    freeze_p.set_defaults(func=_cmd_freeze)

    inspect_p = sub.add_parser("inspect", help="inspect shape, node, manifest, and capability data")
    inspect_p.add_argument("flow_json")
    inspect_p.add_argument("--manifest")
    inspect_p.add_argument("--caps")
    inspect_p.set_defaults(func=_cmd_inspect)

    run_p = sub.add_parser(
        "run-local",
        help="run a flow with in-memory echo stubs; external effects are not performed",
    )
    run_p.add_argument("flow_json")
    run_p.add_argument("input_json")
    run_p.set_defaults(func=_cmd_run_local)

    graph_p = sub.add_parser("graph", help="emit Graphviz DOT for the IR tree")
    graph_p.add_argument("flow_json")
    graph_p.set_defaults(func=_cmd_graph)

    return parser


def _cmd_validate(args: argparse.Namespace, out: TextIO) -> int:
    flow = _load_flow(args.flow_json)
    manifest = _load_manifest(args.manifest) if args.manifest else None
    diagnostics = validate(flow, manifest)
    print(explain(diagnostics), file=out)
    return 1 if blocking(diagnostics) else 0


def _cmd_freeze(args: argparse.Namespace, out: TextIO) -> int:
    flow = _load_flow(args.flow_json)
    snapshot = _load_snapshot(args.snapshot_json)
    caps = _load_caps(args.caps) if args.caps else None
    deployment = deploy(flow, snapshot, capabilities=caps, strict=False)

    _print_json_section(out, "frozen_flow", deployment.flow_json)
    _print_json_section(out, "manifest", deployment.manifest_json)
    if caps is not None:
        print(f"artifact_hash: {deployment.artifact_hash}", file=out)
    print("diagnostics:", file=out)
    print(explain(deployment.diagnostics), file=out)
    return 1 if blocking(deployment.diagnostics) else 0


def _cmd_inspect(args: argparse.Namespace, out: TextIO) -> int:
    flow = _load_flow(args.flow_json)
    manifest = _load_manifest(args.manifest) if args.manifest else {}
    caps = _load_caps(args.caps) if args.caps else None

    print(f"surface_shape: {surface_shape(flow).value}", file=out)
    print(f"closed_shape: {closed_shape(flow).value}", file=out)
    print("nodes:", file=out)
    for line in _node_summary(flow):
        print(line, file=out)

    print(f"manifest_tool_count: {len(manifest)}", file=out)
    for h in sorted(manifest):
        tool = manifest[h]
        print(f"- {h} ref={toolref_key(tool.ref)} definition={tool.definition_hash}", file=out)

    if caps is not None:
        diagnostics = _deploy_diagnostics(flow, manifest, caps)
        deployment = Deployment(
            flow=flow,
            manifest=manifest,
            diagnostics=diagnostics,
            capabilities=caps,
        )
        print(f"artifact_hash: {deployment.artifact_hash}", file=out)
        print("deploy_diagnostics:", file=out)
        print(explain(diagnostics), file=out)
        return 1 if blocking(diagnostics) else 0

    return 0


def _cmd_run_local(args: argparse.Namespace, out: TextIO) -> int:
    flow = _load_flow(args.flow_json)
    _clear_frozen_hashes(flow)
    input_value = _load_json(args.input_json)

    diagnostics = validate(flow)
    bad = blocking(diagnostics)
    if bad:
        print(explain(diagnostics), file=out)
        return 1

    store = InMemoryProjection()
    env = InMemoryEnv(
        {},
        ProjectionEmitter(store),
        hands=_echo_hands(flow),
        brains=_echo_brains(flow),
        subs=_echo_subs(flow),
        agents=_echo_agents(flow),
        gate=lambda value: {"approved": True, "input": value},
    )

    result = asyncio.run(interpret(flow, input_value, env))
    payload = {
        "result": result.value,
        "cost_by_shape": _cost_by_shape_with_zeroes(store),
    }
    _print_json(out, payload)
    return 0


def _cmd_graph(args: argparse.Namespace, out: TextIO) -> int:
    flow = _load_flow(args.flow_json)
    print(graph_dot(flow), file=out)
    return 0


def graph_dot(flow: Node) -> str:
    """Render a Graphviz DOT graph for an IR tree."""
    lines = ["digraph composable_agents {"]
    lines.append("  node [shape=box];")
    seen: set[str] = set()

    def rec(node: Node) -> None:
        if node.id in seen:
            return
        seen.add(node.id)
        label = f"{node.id}\\n{node.op.value}\\n{surface_shape(node).value}"
        lines.append(f"  {_dot_id(node.id)} [label={json.dumps(label)}];")

        children = _graph_children(node)
        for edge_label, child in children:
            lines.append(
                f"  {_dot_id(node.id)} -> {_dot_id(child.id)} [label={json.dumps(edge_label)}];"
            )
            rec(child)

        if isinstance(node.step, SubStep):
            sub_id = f"{node.id}::sub::{node.step.ref}"
            label = f"sub:{node.step.ref}\\n{node.step.contract.shape.value}"
            lines.append(
                f"  {_dot_id(sub_id)} [label={json.dumps(label)}, style=dashed];"
            )
            lines.append(
                f"  {_dot_id(node.id)} -> {_dot_id(sub_id)} [label=\"sub\", style=dashed];"
            )

    rec(flow)
    lines.append("}")
    return "\n".join(lines)


def _graph_children(node: Node) -> list[tuple[str, Node]]:
    out: list[tuple[str, Node]] = []
    if node.op in {Op.SEQ, Op.PAR}:
        if node.left is not None:
            out.append(("left", node.left))
        if node.right is not None:
            out.append(("right", node.right))
    elif node.op == Op.ALT:
        if node.cases is not None:
            for key in sorted(node.cases):
                out.append((f"case:{key}", node.cases[key]))
            if node.default is not None:
                out.append(("default", node.default))
        else:
            if node.left is not None:
                out.append(("true", node.left))
            if node.right is not None:
                out.append(("false", node.right))
    elif node.op == Op.ITER_UP_TO:
        if node.body is not None:
            out.append(("body", node.body))
    elif node.op == Op.EVAL_PLAN:
        if node.plan is not None:
            out.append(("plan", node.plan))
    return out


def _node_summary(flow: Node) -> list[str]:
    lines: list[str] = []

    def rec(node: Node, depth: int) -> None:
        indent = "  " * depth
        lines.append(
            f"{indent}- {node.id}: op={node.op.value} "
            f"surface={surface_shape(node).value} closed={closed_shape(node).value}"
        )
        for _label, child in _graph_children(node):
            rec(child, depth + 1)

    rec(flow, 0)
    return lines


def _deploy_diagnostics(
    flow: Node,
    manifest: ToolManifest,
    caps: CapabilityManifest,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(validate(flow, manifest))
    diagnostics.extend(caps.enforce_compile(flow, manifest))
    diagnostics.extend(check_approval_gates(flow, manifest, caps))
    diagnostics.extend(check_race_admission(flow, manifest))
    return diagnostics


def _load_flow(path: str | Path) -> Node:
    return Node.from_json(_load_json(path))


def _load_manifest(path: str | Path) -> ToolManifest:
    return manifest_from_json(_load_json(path))


def _load_caps(path: str | Path) -> CapabilityManifest:
    return CapabilityManifest.from_file(str(path))


def _load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_snapshot(path: str | Path) -> McpSnapshot:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("snapshot JSON must be an object")

    if "listings" in payload:
        snapshot = snapshot_from_listings(
            payload.get("listings") or {},
            versions=payload.get("versions") or {},
        )
        if payload.get("native"):
            return McpSnapshot(
                servers=snapshot.servers,
                native=_native_specs(payload["native"]),
            )
        return snapshot

    if "servers" in payload or "native" in payload:
        return McpSnapshot(
            servers=_server_specs(payload.get("servers") or {}),
            native=_native_specs(payload.get("native") or {}),
        )

    return snapshot_from_listings(payload)


def _server_specs(raw: dict[str, Any]) -> dict[str, McpServerSnapshot]:
    servers: dict[str, McpServerSnapshot] = {}
    for server_name, server_payload in raw.items():
        if not isinstance(server_payload, dict):
            raise ValueError(f"server {server_name!r} must be an object")
        tools_payload = server_payload.get("tools", server_payload)
        if not isinstance(tools_payload, dict):
            raise ValueError(f"server {server_name!r} tools must be an object")
        tools: dict[str, McpToolSpec] = {}
        for tool_name, spec in tools_payload.items():
            tools[tool_name] = _mcp_tool_spec(spec)
        servers[server_name] = McpServerSnapshot(
            server=server_name,
            version=server_payload.get("version"),
            tools=tools,
        )
    return servers


def _mcp_tool_spec(raw: dict[str, Any]) -> McpToolSpec:
    if not isinstance(raw, dict):
        raise ValueError("MCP tool spec must be an object")
    return McpToolSpec(
        input_schema=raw.get("inputSchema", raw.get("input_schema", {})),
        annotations=McpAnnotations.from_mcp(raw.get("annotations", raw)),
        output_schema=raw.get("outputSchema", raw.get("output_schema")),
    )


def _native_specs(raw: dict[str, Any]) -> dict[str, NativeToolSpec]:
    native: dict[str, NativeToolSpec] = {}
    for name, spec in raw.items():
        if not isinstance(spec, dict):
            raise ValueError(f"native tool {name!r} must be an object")
        native[name] = NativeToolSpec(
            input_schema=spec.get("inputSchema", spec.get("input_schema", {})),
            contract=ToolContract.from_json(spec["contract"]),
            output_schema=spec.get("outputSchema", spec.get("output_schema")),
        )
    return native


def _clear_frozen_hashes(flow: Node) -> None:
    for node in flow.walk():
        step = node.step
        if isinstance(step, CallStep):
            step.frozen_hash = None


def _echo_hands(flow: Node) -> dict[str, Any]:
    hands: dict[str, Any] = {}
    for ref in flow.tool_refs():
        hands[toolref_key(ref)] = lambda value: value
    return hands


def _echo_brains(flow: Node) -> dict[str, Any]:
    brains: dict[str, Any] = {}
    for node in flow.walk():
        step = node.step
        brain = getattr(step, "brain", None)
        if brain is not None:
            brains[brain] = lambda value: value
        if node.op in {Op.APP, Op.EVAL_PLAN} and node.controller is not None:
            brains[node.controller] = lambda value: value
    return brains


def _echo_subs(flow: Node) -> dict[str, Any]:
    subs: dict[str, Any] = {}
    for node in flow.walk():
        if isinstance(node.step, SubStep):
            subs[node.step.ref] = lambda value: value
    return subs


def _echo_agents(flow: Node) -> dict[str, Any]:
    agents: dict[str, Any] = {}
    for node in flow.walk():
        if node.op == Op.APP and node.controller is not None:
            agents[node.controller] = lambda value: value
    return agents


def _cost_by_shape_with_zeroes(store: InMemoryProjection) -> dict[str, float]:
    costs = store.cost_by_shape()
    for event in store.events():
        if event.type == EventType.DID and event.shape is not None:
            costs.setdefault(event.shape, 0.0)
    return costs


def _print_json_section(out: TextIO, name: str, payload: Any) -> None:
    print(f"{name}:", file=out)
    _print_json(out, payload)


def _print_json(out: TextIO, payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True), file=out)


def _dot_id(raw: str) -> str:
    return "n_" + "".join(ch if ch.isalnum() else "_" for ch in raw)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
