"""Run a composable agent against a local or Temporal-backed environment."""

from __future__ import annotations

import asyncio
import inspect
import uuid
from collections.abc import Callable
from typing import Any

from composable_agents.ca.config import CaConfig, EnvConfig
from composable_agents.ca.ledger import read_ledger
from composable_agents.ca.resolve import resolve_agent
from composable_agents.ca.runner import run_agent_local

__all__ = ["run_on_env"]


def run_on_env(
    cfg: CaConfig,
    name: str,
    env: EnvConfig,
    value: Any,
    *,
    run_id: str | None = None,
    client: Any | None = None,
    run_flow: Callable[..., Any] | None = None,
) -> Any:
    """Run an agent locally or through the deployed Temporal environment."""

    if _is_local_env(env):
        resolved = resolve_agent(cfg, name)
        return run_agent_local(resolved, value, run_id=run_id or _local_run_id())

    records = read_ledger(cfg.root, env.name)
    if name not in records:
        raise ValueError(
            f"agent {name!r} is not deployed to env {env.name!r}; "
            f"run: ca deploy {name} --env {env.name}"
        )

    record = records[name]
    session_id = run_id or _temporal_session_id(name, env.name)
    run_flow_callable = run_flow or _load_run_flow()
    temporal_client = client if client is not None else _connect_temporal_client(env)

    result = run_flow_callable(
        temporal_client,
        record.flow_json,
        record.manifest_json,
        session_id=session_id,
        input=value,
        task_queue=env.task_queue,
        bundle=record.bundle_ref,
    )
    return _await_if_needed(result)


def _is_local_env(env: EnvConfig) -> bool:
    return env.name == "local" or env.temporal_address is None


def _local_run_id() -> str:
    return f"ca-local-{uuid.uuid4().hex[:12]}"


def _temporal_session_id(name: str, env_name: str) -> str:
    return f"ca-{name}-{env_name}-{uuid.uuid4().hex[:12]}"


def _load_run_flow() -> Callable[..., Any]:
    from composable_agents.execution.harness import run_flow as _run_flow

    return _run_flow


def _connect_temporal_client(env: EnvConfig) -> Any:
    if env.temporal_address is None:
        raise ValueError(f"env {env.name!r} has no temporal_address")

    try:
        from temporalio.client import Client
    except ImportError as exc:
        raise RuntimeError(
            "Temporal support is not installed; install the temporal extra with "
            "pip install 'composable-agents[temporal]'"
        ) from exc

    return asyncio.run(
        Client.connect(env.temporal_address, namespace=env.temporal_namespace)
    )


def _await_if_needed(result: Any) -> Any:
    if inspect.isawaitable(result):
        return asyncio.run(_await_result(result))
    return result


async def _await_result(result: Any) -> Any:
    return await result
