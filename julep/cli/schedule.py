"""Temporal schedule management for julep.toml schedules.

The 24 APScheduler jobs become `[schedule.*]` tables; SQL-trigger enqueues
(summary) stay app-side ingress, out of scope.

Queue lanes are deployment topology, not artifact identity: real mem-mcp role
lanes map to one worker Deployment + KEDA ScaledObject per lane. Interactive
(RECORD plan/execute, checkin/recall) vs background (sweeps, rollups,
clustering, dream) is the two-lane starter, not the ceiling.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from julep.cli.config import JulepConfig, EnvConfig, ScheduleConfig
from julep.cli.ledger import DeployRecord, read_ledger
from julep.cli.temporal_run import (
    build_flow_input_kwargs,
    build_flow_start_args,
    connect_temporal_client,
)


def schedule_id(env: str, name: str) -> str:
    return f"julep:{env}:{name}"


# Temporal normalizes cron expressions into a structured calendar spec server-side,
# so `spec.cron_expressions` reads back empty. We round-trip the desired cron through
# the schedule note (which, unlike memo, survives BOTH create and update) so drift
# detection can compare the configured cron against what is actually on the server.
_NOTE_CRON_PREFIX = "julep-managed cron="


def _schedule_note(cron: str) -> str:
    return f"{_NOTE_CRON_PREFIX}{cron}"


def _cron_from_note(note: object) -> str | None:
    if isinstance(note, str) and note.startswith(_NOTE_CRON_PREFIX):
        return note[len(_NOTE_CRON_PREFIX):]
    return None


def schedules_for_env(cfg: JulepConfig, env_name: str) -> list[ScheduleConfig]:
    return sorted(
        [sched for sched in cfg.schedules.values() if sched.env == env_name],
        key=lambda sched: sched.name,
    )


@dataclass(frozen=True)
class ScheduleDriftRow:
    name: str
    schedule_id: str
    state: str
    detail: str = ""


def schedule_drift(
    env_name: str,
    configured: list[ScheduleConfig],
    server: dict[str, dict[str, Any]],
) -> list[ScheduleDriftRow]:
    rows: list[ScheduleDriftRow] = []
    configured_by_id: dict[str, ScheduleConfig] = {
        schedule_id(env_name, sched.name): sched
        for sched in sorted(configured, key=lambda item: schedule_id(env_name, item.name))
    }

    for sid, sched in configured_by_id.items():
        server_row = server.get(sid)
        if server_row is None:
            rows.append(
                ScheduleDriftRow(
                    name=sched.name,
                    schedule_id=sid,
                    state="missing",
                    detail="not on server; run: julep schedule apply",
                )
            )
            continue

        server_cron = server_row.get("cron")
        server_paused = bool(server_row.get("paused", False))
        if server_cron != sched.cron or server_paused != sched.paused:
            rows.append(
                ScheduleDriftRow(
                    name=sched.name,
                    schedule_id=sid,
                    state="drift",
                    detail=f"server cron={server_cron!r} paused={server_paused!r}",
                )
            )
            continue

        rows.append(ScheduleDriftRow(name=sched.name, schedule_id=sid, state="in-sync"))

    prefix = f"julep:{env_name}:"
    for sid in sorted(server):
        if not sid.startswith(prefix) or sid in configured_by_id:
            continue
        rows.append(
            ScheduleDriftRow(
                name=sid.removeprefix(prefix),
                schedule_id=sid,
                state="orphan",
                detail="on server but not in config",
            )
        )

    return rows


def build_schedule(
    record: DeployRecord,
    env: EnvConfig,
    sched: ScheduleConfig,
    *,
    mcp_preflight_policy: str = "pin",
) -> Any:
    from julep.execution.harness import (
        FlowWorkflow,
        build_flow_input,
    )
    from temporalio.client import (
        Schedule,
        ScheduleActionStartWorkflow,
        ScheduleOverlapPolicy,
        SchedulePolicy,
        ScheduleSpec,
        ScheduleState,
    )

    sa = build_flow_start_args(
        record,
        env,
        sched.input,
        mcp_preflight_policy=mcp_preflight_policy,
    )
    flow_input = build_flow_input(**build_flow_input_kwargs(sa, session_id=sa.session_id))
    action = ScheduleActionStartWorkflow(
        FlowWorkflow.run,
        args=[flow_input],
        id=schedule_id(env.name, sched.name),
        task_queue=sa.task_queue,
    )
    spec = ScheduleSpec(cron_expressions=[sched.cron])
    policy = SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP)
    state = ScheduleState(paused=sched.paused, note=_schedule_note(sched.cron))
    return Schedule(action=action, spec=spec, policy=policy, state=state)


def apply_schedules(
    cfg: JulepConfig,
    env: EnvConfig,
    schedules: list[ScheduleConfig],
    *,
    client: Any | None = None,
) -> list[tuple[str, str]]:
    records = read_ledger(cfg.root, env.name)
    for sched in schedules:
        if sched.flow not in records:
            raise ValueError(
                f"flow {sched.flow!r} (schedule {sched.name!r}) is not deployed to env "
                f"{env.name!r}; run: julep deploy {sched.flow} --env {env.name}"
            )

    temporal_client = client if client is not None else connect_temporal_client(env)
    return asyncio.run(
        _apply_all(
            temporal_client,
            records,
            env,
            schedules,
            mcp_preflight_policy=cfg.mcp_preflight,
        )
    )


async def _apply_all(
    client: Any,
    records: dict[str, DeployRecord],
    env: EnvConfig,
    schedules: list[ScheduleConfig],
    *,
    mcp_preflight_policy: str = "pin",
) -> list[tuple[str, str]]:
    from temporalio.client import ScheduleAlreadyRunningError, ScheduleUpdate

    results: list[tuple[str, str]] = []
    for sched in schedules:
        sid = schedule_id(env.name, sched.name)
        obj = build_schedule(
            records[sched.flow],
            env,
            sched,
            mcp_preflight_policy=mcp_preflight_policy,
        )
        try:
            await client.create_schedule(sid, obj)
            action = "created"
        except ScheduleAlreadyRunningError:
            handle = client.get_schedule_handle(sid)
            await handle.update(lambda _in, obj=obj: ScheduleUpdate(schedule=obj))
            action = "updated"
        results.append((sched.name, action))
    return results


def remove_schedule(env: EnvConfig, name: str, *, client: Any | None = None) -> bool:
    temporal_client = client if client is not None else connect_temporal_client(env)
    return asyncio.run(_remove_schedule(temporal_client, env, name))


async def _remove_schedule(client: Any, env: EnvConfig, name: str) -> bool:
    from temporalio.service import RPCError, RPCStatusCode

    try:
        await client.get_schedule_handle(schedule_id(env.name, name)).delete()
    except RPCError as exc:
        if exc.status == RPCStatusCode.NOT_FOUND:
            return False
        raise
    return True


def fetch_server_schedules(
    env: EnvConfig,
    *,
    client: Any | None = None,
) -> dict[str, dict[str, Any]]:
    temporal_client = client if client is not None else connect_temporal_client(env)
    return asyncio.run(_fetch_server_schedules(temporal_client))


async def _fetch_server_schedules(client: Any) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    schedule_iter = await client.list_schedules()
    async for sched in schedule_iter:
        sid = str(sched.id)
        schedule = getattr(sched, "schedule", None)
        state = getattr(schedule, "state", None)
        note = getattr(state, "note", None)
        cron = _cron_from_note(note)
        rows[sid] = {
            "cron": cron,
            "paused": bool(getattr(state, "paused", False)),
        }
    return rows
