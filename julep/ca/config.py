from __future__ import annotations

import sys
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from julep.ca.queues import resolve_queue_lane as resolve_queue_lane

if sys.version_info >= (3, 11):
    import tomllib as _tomllib
else:
    _tomllib = None

_CRON_TOKEN_RE = re.compile(r"^[0-9*/,\-A-Za-z?]+$")


@dataclass(frozen=True)
class EnvConfig:
    name: str
    temporal_address: str | None = None
    temporal_namespace: str = 'default'
    task_queue: str = 'julep'
    cas: str | None = None
    langfuse_host: str | None = None
    # [env.<name>.vars]: the env profile bound as the dotctx yglu default env
    # inside the resolver/freeze child (never the ambient process environment).
    vars: dict[str, str] = field(default_factory=dict)
    queues: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ScheduleConfig:
    name: str
    cron: str
    flow: str
    input: Any = None
    env: str = "local"
    paused: bool = False


@dataclass(frozen=True)
class CaConfig:
    root: Path
    src: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    tags: dict[str, list[str]] = field(default_factory=dict)
    # Discovered flow/agent name -> lane name. Resolved through [env.<env>.queues]
    # at run/start time; distinct from EnvConfig.queues (lane -> concrete queue).
    flow_queues: dict[str, str] = field(default_factory=dict)
    fail_severity: str = 'error'
    envs: dict[str, EnvConfig] = field(default_factory=dict)
    schedules: dict[str, ScheduleConfig] = field(default_factory=dict)


def validate_cron(cron: str) -> None:
    fields = cron.split()
    if len(fields) not in (5, 6):
        raise ValueError(
            f"cron {cron!r} must have 5 or 6 whitespace-separated fields "
            f"(minute hour day-of-month month day-of-week [year]); got {len(fields)}"
        )
    for token in fields:
        if not _CRON_TOKEN_RE.match(token):
            raise ValueError(f"cron field {token!r} in {cron!r} is not a valid cron token")


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    if _tomllib is None:
        raise RuntimeError('reading TOML requires Python 3.11 or newer')
    with path.open('rb') as fh:
        data: dict[str, Any] = _tomllib.load(fh)
        return data


def _env_fields(table: object) -> dict[str, str | None]:
    if not isinstance(table, dict):
        return {}
    fields: dict[str, str | None] = {}
    for key in (
        'temporal_address',
        'temporal_namespace',
        'task_queue',
        'cas',
        'langfuse_host',
    ):
        if key in table:
            value = table[key]
            fields[key] = None if value is None else str(value)
    return fields


def _env_vars(table: object) -> dict[str, str]:
    if not isinstance(table, dict):
        return {}
    raw = table.get('vars')
    if not isinstance(raw, dict):
        return {}
    return {str(key): str(value) for key, value in raw.items()}


def _env_queues(table: object) -> dict[str, str]:
    if not isinstance(table, dict):
        return {}
    raw = table.get('queues')
    if not isinstance(raw, dict):
        return {}
    return {str(key): str(value) for key, value in raw.items()}


def _flow_queues(pyproject_queue: object, ca_toml_queue: object) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in (pyproject_queue, ca_toml_queue):
        if isinstance(raw, dict):
            for key, value in raw.items():
                out[str(key)] = str(value)
    return out


def _build_envs(
    root: Path,
    pyproject_envs: object,
    ca_toml_envs: object,
) -> dict[str, EnvConfig]:
    env_tables: dict[str, dict[str, str | None]] = {}
    env_vars: dict[str, dict[str, str]] = {}
    env_queues: dict[str, dict[str, str]] = {}
    for raw_envs in (pyproject_envs, ca_toml_envs):
        if not isinstance(raw_envs, dict):
            continue
        for name, table in raw_envs.items():
            env_name = str(name)
            env_tables.setdefault(env_name, {}).update(_env_fields(table))
            # vars merge per-key, ca.toml over pyproject (scalar-field order).
            env_vars.setdefault(env_name, {}).update(_env_vars(table))
            env_queues.setdefault(env_name, {}).update(_env_queues(table))

    local_defaults: dict[str, str | None] = {
        'cas': str(root / '.ca' / 'cas'),
        'temporal_address': None,
    }
    env_tables['local'] = {**local_defaults, **env_tables.get('local', {})}

    return {
        name: EnvConfig(
            name=name,
            temporal_address=fields.get('temporal_address'),
            temporal_namespace=fields.get('temporal_namespace') or 'default',
            task_queue=fields.get('task_queue') or 'julep',
            cas=fields.get('cas'),
            langfuse_host=fields.get('langfuse_host'),
            vars=env_vars.get(name, {}),
            queues=env_queues.get(name, {}),
        )
        for name, fields in env_tables.items()
    }


def _build_schedules(
    pyproject_sched: object,
    ca_toml_sched: object,
) -> dict[str, ScheduleConfig]:
    tables: dict[str, dict[str, Any]] = {}
    for raw_schedules in (pyproject_sched, ca_toml_sched):
        if not isinstance(raw_schedules, dict):
            continue
        for name, table in raw_schedules.items():
            sched_name = str(name)
            if isinstance(table, dict):
                tables.setdefault(sched_name, {}).update(table)
            else:
                tables.setdefault(sched_name, {})

    schedules: dict[str, ScheduleConfig] = {}
    for name, table in tables.items():
        cron = table.get("cron")
        if not isinstance(cron, str) or not cron:
            raise ValueError(f"schedule {name!r} requires a 'cron' string")
        flow = table.get("flow")
        if not isinstance(flow, str) or not flow:
            raise ValueError(f"schedule {name!r} requires a 'flow' string")
        validate_cron(cron)
        env_value = table.get("env", "local")
        if not isinstance(env_value, str):
            raise ValueError(
                f"schedule {name!r} field 'env' must be a string, "
                f"got {type(env_value).__name__}"
            )
        paused_value = table.get("paused", False)
        if not isinstance(paused_value, bool):
            raise ValueError(
                f"schedule {name!r} field 'paused' must be a boolean (true/false), "
                f"got {type(paused_value).__name__}"
            )
        schedules[name] = ScheduleConfig(
            name=name,
            cron=cron,
            flow=flow,
            input=table.get("input"),
            env=env_value,
            paused=paused_value,
        )
    return schedules


def load_config(root: str | Path) -> CaConfig:
    """Read [tool.ca] from pyproject.toml, then overlay a sibling ca.toml if present."""
    root = Path(root)
    pyproject = _read_toml(root / 'pyproject.toml').get('tool', {}).get('ca', {})
    ca_toml = _read_toml(root / 'ca.toml')
    merged: dict[str, Any] = {**pyproject, **ca_toml}
    gates = {**pyproject.get('gates', {}), **ca_toml.get('gates', {})}
    return CaConfig(
        root=root,
        src=list(merged.get('src', [str(root)])),
        exclude=list(merged.get('exclude', [])),
        tags={k: list(v) for k, v in merged.get('tags', {}).items()},
        flow_queues=_flow_queues(pyproject.get('queue', {}), ca_toml.get('queue', {})),
        fail_severity=str(gates.get('fail_severity', 'error')),
        envs=_build_envs(root, pyproject.get('env', {}), ca_toml.get('env', {})),
        schedules=_build_schedules(pyproject.get("schedule", {}), ca_toml.get("schedule", {})),
    )
