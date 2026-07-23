from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from julep.cli.config import JulepConfig


@dataclass(frozen=True)
class AgentInfo:
    name: str
    kind: str
    file: str
    line: int
    calls: list[str] = field(default_factory=list)


def scan_agents(cfg: JulepConfig) -> list[AgentInfo]:
    """Find top-level @flow functions and Agent(...) assignments without imports."""
    flow_names: set[str] = set()
    raw: list[tuple[ast.AST, str, str, str, int]] = []

    for path in _iter_files(cfg):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                _is_flow_decorator(dec) for dec in node.decorator_list
            ):
                flow_names.add(node.name)
                raw.append((node, node.name, "flow", str(path), node.lineno))
            elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and _is_agent_call(node.value):
                name = _agent_name_kwarg(node.value) or _assignment_target_name(node) or "agent"
                raw.append((node, name, "agent", str(path), node.lineno))

    return [
        AgentInfo(
            name=name,
            kind=kind,
            file=file,
            line=line,
            calls=sorted(call for call in _called_names(node) if call in flow_names and call != name),
        )
        for node, name, kind, file, line in raw
    ]


def _iter_files(cfg: JulepConfig) -> list[Path]:
    files: list[Path] = []
    for entry in cfg.src:
        base = (cfg.root / entry).resolve()
        if base.is_file() and base.suffix == ".py":
            files.append(base)
        elif base.is_dir():
            files.extend(path.resolve() for path in base.rglob("*.py") if path.name != "__init__.py")

    excluded = _excluded_files(cfg)
    return [path for path in files if path not in excluded]


def _excluded_files(cfg: JulepConfig) -> set[Path]:
    excluded: set[Path] = set()
    for pattern in cfg.exclude:
        excluded.update(path.resolve() for path in cfg.root.glob(pattern))
        for entry in cfg.src:
            base = (cfg.root / entry).resolve()
            if base.is_dir():
                excluded.update(path.resolve() for path in base.rglob(pattern))
    return excluded


def _is_flow_decorator(decorator: ast.expr) -> bool:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    return (isinstance(target, ast.Name) and target.id == "flow") or (
        isinstance(target, ast.Attribute) and target.attr == "flow"
    )


def _is_agent_call(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Name) and call.func.id == "Agent"


def _agent_name_kwarg(call: ast.Call) -> str | None:
    for keyword in call.keywords:
        if (
            keyword.arg == "name"
            and isinstance(keyword.value, ast.Constant)
            and isinstance(keyword.value.value, str)
        ):
            return keyword.value.value
    return None


def _assignment_target_name(assign: ast.Assign) -> str | None:
    for target in assign.targets:
        if isinstance(target, ast.Name):
            return target.id
    return None


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for subnode in ast.walk(node):
        if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
            names.add(subnode.func.id)
    return names
