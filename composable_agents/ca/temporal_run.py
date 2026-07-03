"""Run a composable agent against a local or Temporal-backed environment."""

from __future__ import annotations

import asyncio
import inspect
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from composable_agents.ca.config import CaConfig, EnvConfig
from composable_agents.ca.ledger import DeployRecord, read_ledger
from composable_agents.ca.queues import resolve_queue_lane
from composable_agents.ca.runner import run_agent_local

__all__ = [
    "FlowStartArgs",
    "build_flow_input_kwargs",
    "build_flow_start_args",
    "connect_temporal_client",
    "run_on_env",
]


@dataclass(frozen=True)
class FlowStartArgs:
    flow_json: dict[str, Any]
    manifest_json: dict[str, Any]
    session_id: str
    input: Any
    task_queue: str
    bundle: list[dict[str, Any]] | None
    pinned_pures: dict[str, str] | None
    queue_lanes: dict[str, str] | None = None


def build_flow_start_args(record: DeployRecord, env: EnvConfig, input: Any) -> FlowStartArgs:
    """Single reader of a deploy record + env into workflow-start primitives.

    Used by BOTH the deployed-run seam (``run_on_env``) and ``ca schedule apply``,
    so a scheduled run replays the deployed artifact + its pinned pures
    byte-identically to a manual ``ca run``. ``session_id`` is a deterministic
    base; the run path overrides it with a per-run id, the schedule path uses it
    as the trajectory root base.
    """
    return FlowStartArgs(
        flow_json=record.flow_json,
        manifest_json=record.manifest_json,
        session_id=f"ca:{env.name}:{record.agent}",
        input=input,
        task_queue=resolve_queue_lane(record.queue, env.queues, env.task_queue),
        bundle=record.bundle_ref,
        pinned_pures=record.pinned_pures or None,
        queue_lanes=(env.queues or None),
    )


def build_flow_input_kwargs(sa: FlowStartArgs, *, session_id: str) -> dict[str, Any]:
    """The ONE mapping from start-args to FlowInput construction kwargs.

    Both the deployed-run seam (``run_on_env`` -> ``run_flow``) and ``ca schedule``
    (``build_schedule`` -> ``build_flow_input``) construct their FlowInput from this
    single dict, so any field added here reaches BOTH paths. ``task_queue`` is NOT
    included: it is a workflow-start parameter, not a FlowInput field.
    """
    return {
        "session_id": session_id,
        "input": sa.input,
        "flow_json": sa.flow_json,
        "manifest_json": sa.manifest_json,
        "pinned_pures": sa.pinned_pures,
        "bundle": sa.bundle,
        "queue_lanes": sa.queue_lanes,
    }


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

    if env.name == "local":
        return run_agent_local(
            cfg, name, value, run_id=run_id or _local_run_id(), env_vars=env.vars
        )

    # A deliberately non-local env MUST have a Temporal address; otherwise we'd
    # silently re-run live source instead of the deployed artifact (immutability
    # violation). Fail loud rather than fall back to the in-memory path.
    if env.temporal_address is None:
        raise ValueError(
            f"env {env.name!r} has no temporal_address; cannot run the deployed "
            f"artifact remotely"
        )

    records = read_ledger(cfg.root, env.name)
    if name not in records:
        raise ValueError(
            f"agent {name!r} is not deployed to env {env.name!r}; "
            f"run: ca deploy {name} --env {env.name}"
        )

    record = records[name]
    session_id = run_id or _temporal_session_id(name, env.name)
    run_flow_callable = run_flow or _load_run_flow()
    temporal_client = client if client is not None else connect_temporal_client(env)

    sa = build_flow_start_args(record, env, value)
    result = run_flow_callable(
        temporal_client,
        task_queue=sa.task_queue,
        **build_flow_input_kwargs(sa, session_id=session_id),
    )
    return _await_if_needed(result)


def _local_run_id() -> str:
    return f"ca-local-{uuid.uuid4().hex[:12]}"


def _temporal_session_id(name: str, env_name: str) -> str:
    return f"ca-{name}-{env_name}-{uuid.uuid4().hex[:12]}"


def _load_run_flow() -> Callable[..., Any]:
    from composable_agents.execution.harness import run_flow as _run_flow

    return _run_flow


def connect_temporal_client(env: EnvConfig) -> Any:
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
