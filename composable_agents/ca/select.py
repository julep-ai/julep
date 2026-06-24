from __future__ import annotations

import fnmatch
from pathlib import Path

from composable_agents.ca.gitstate import modified_agent_files
from composable_agents.ca.model import Agent, Module


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
        from composable_agents.ca.runcache import failed_agents

        failed = failed_agents(module.root)
        return {agent.name for agent in module.agents if agent.name in failed}

    return {agent.name for agent in module.agents if agent.name == token}


def _eval_expr(module: Module, expr: str, *, state_ref: str) -> set[str]:
    if not expr.strip():
        return {agent.name for agent in module.agents}

    selected: set[str] = set()
    for group in expr.split():
        group_selected: set[str] | None = None
        for token in (part for part in group.split(",") if part):
            token_matches = _match_method(module, token, state_ref=state_ref)
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
