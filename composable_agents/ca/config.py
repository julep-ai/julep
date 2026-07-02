from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib as _tomllib
else:
    _tomllib = None


@dataclass(frozen=True)
class EnvConfig:
    name: str
    temporal_address: str | None = None
    temporal_namespace: str = 'default'
    task_queue: str = 'composable-agents'
    cas: str | None = None
    langfuse_host: str | None = None
    # [env.<name>.vars]: the env profile bound as the dotctx yglu default env
    # inside the resolver/freeze child (never the ambient process environment).
    vars: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CaConfig:
    root: Path
    src: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    tags: dict[str, list[str]] = field(default_factory=dict)
    fail_severity: str = 'error'
    envs: dict[str, EnvConfig] = field(default_factory=dict)


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


def _build_envs(
    root: Path,
    pyproject_envs: object,
    ca_toml_envs: object,
) -> dict[str, EnvConfig]:
    env_tables: dict[str, dict[str, str | None]] = {}
    env_vars: dict[str, dict[str, str]] = {}
    for raw_envs in (pyproject_envs, ca_toml_envs):
        if not isinstance(raw_envs, dict):
            continue
        for name, table in raw_envs.items():
            env_name = str(name)
            env_tables.setdefault(env_name, {}).update(_env_fields(table))
            # vars merge per-key, ca.toml over pyproject (scalar-field order).
            env_vars.setdefault(env_name, {}).update(_env_vars(table))

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
            task_queue=fields.get('task_queue') or 'composable-agents',
            cas=fields.get('cas'),
            langfuse_host=fields.get('langfuse_host'),
            vars=env_vars.get(name, {}),
        )
        for name, fields in env_tables.items()
    }


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
        fail_severity=str(gates.get('fail_severity', 'error')),
        envs=_build_envs(root, pyproject.get('env', {}), ca_toml.get('env', {})),
    )
