from __future__ import annotations

from collections import deque
import fnmatch
import re
from pathlib import Path

from julep.ca.gitstate import modified_agent_files
from julep.ca.model import Agent, Module

_LEADING_GRAPH_OPERATOR_RE = re.compile(r"^(\d+)\+")
_TRAILING_GRAPH_OPERATOR_RE = re.compile(r"\+(\d+)$")


def _agent_relative_file(module: Module, agent: Agent) -> str:
    path = _agent_resolved_file(module, agent)
    root = Path(module.root).resolve()

    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _agent_resolved_file(module: Module, agent: Agent) -> Path:
    root = Path(module.root).resolve()
    path = Path(agent.file)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _match_method(module: Module, token: str, *, state_ref: str) -> set[str]:
    if token.startswith("tag:"):
        tag = token.removeprefix("tag:")
        return {agent.name for agent in module.agents if tag in agent.tags}

    if token.startswith("path:"):
        pattern = token.removeprefix("path:")
        return {
            agent.name
            for agent in module.agents
            if fnmatch.fnmatch(_agent_relative_file(module, agent), pattern)
        }

    if token == "state:modified":
        modified = modified_agent_files(module.root, state_ref)
        return {
            agent.name
            for agent in module.agents
            if str(_agent_resolved_file(module, agent)) in modified
        }

    if token == "result:fail":
        from julep.ca.runcache import failed_agents

        failed = failed_agents(module.root)
        return {agent.name for agent in module.agents if agent.name in failed}

    return {agent.name for agent in module.agents if agent.name == token}


def _build_adjacency(module: Module) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    names = {agent.name for agent in module.agents}
    upstream: dict[str, set[str]] = {}
    downstream: dict[str, set[str]] = {name: set() for name in names}

    for agent in module.agents:
        agent_upstream = {name for name in agent.calls if name in names}
        upstream[agent.name] = agent_upstream
        for name in agent_upstream:
            downstream[name].add(agent.name)

    return upstream, downstream


def _closure(
    start: set[str],
    adjacency: dict[str, set[str]],
    max_depth: int | None,
) -> set[str]:
    visited = set(start)
    queue: deque[tuple[str, int]] = deque((name, 0) for name in start)

    while queue:
        name, depth = queue.popleft()
        if max_depth is not None and depth >= max_depth:
            continue

        for neighbor in adjacency[name]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, depth + 1))

    return visited


def _parse_graph_operators(token: str) -> tuple[str, int | None, int | None, bool, bool]:
    upstream_depth: int | None = None
    downstream_depth: int | None = None
    has_upstream = False
    has_downstream = False
    base = token

    leading_match = _LEADING_GRAPH_OPERATOR_RE.match(base)
    if leading_match is not None:
        has_upstream = True
        upstream_depth = int(leading_match.group(1))
        base = base[leading_match.end() :]
    elif base.startswith("+"):
        has_upstream = True
        base = base[1:]

    trailing_match = _TRAILING_GRAPH_OPERATOR_RE.search(base)
    if trailing_match is not None:
        has_downstream = True
        downstream_depth = int(trailing_match.group(1))
        base = base[: trailing_match.start()]
    elif base.endswith("+"):
        has_downstream = True
        base = base[:-1]

    return base, upstream_depth, downstream_depth, has_upstream, has_downstream


def _resolve_token(
    module: Module,
    token: str,
    *,
    state_ref: str,
    upstream: dict[str, set[str]],
    downstream: dict[str, set[str]],
) -> set[str]:
    if token.startswith("@"):
        base = token.removeprefix("@")
        if not base:
            return set()

        start = _match_method(module, base, state_ref=state_ref)
        down = _closure(start, downstream, max_depth=None)
        return down | _closure(down, upstream, max_depth=None)

    base, upstream_depth, downstream_depth, has_upstream, has_downstream = (
        _parse_graph_operators(token)
    )
    if not base:
        return set()

    start = _match_method(module, base, state_ref=state_ref)
    resolved = set(start)
    if has_upstream:
        resolved |= _closure(start, upstream, max_depth=upstream_depth)
    if has_downstream:
        resolved |= _closure(start, downstream, max_depth=downstream_depth)

    return resolved


def _eval_expr(module: Module, expr: str, *, state_ref: str) -> set[str]:
    if not expr.strip():
        return {agent.name for agent in module.agents}

    upstream, downstream = _build_adjacency(module)
    selected: set[str] = set()
    for group in expr.split():
        group_selected: set[str] | None = None
        for token in (part for part in group.split(",") if part):
            token_matches = _resolve_token(
                module,
                token,
                state_ref=state_ref,
                upstream=upstream,
                downstream=downstream,
            )
            if group_selected is None:
                group_selected = token_matches
            else:
                group_selected &= token_matches

        if group_selected is not None:
            selected |= group_selected

    return selected


def select(
    module: Module,
    expr: str,
    *,
    exclude: str = "",
    state_ref: str = "HEAD",
) -> list[Agent]:
    chosen = _eval_expr(module, expr, state_ref=state_ref)
    if exclude:
        chosen -= _eval_expr(module, exclude, state_ref=state_ref)

    return sorted(
        (agent for agent in module.agents if agent.name in chosen),
        key=lambda agent: agent.name,
    )
