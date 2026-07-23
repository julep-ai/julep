from __future__ import annotations

from difflib import get_close_matches
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from julep.cli.queues import resolve_queue_lane as resolve_queue_lane
from julep.ctx_pipeline import CtxPipelineConfig
from julep.execution.policy import ExecutionPolicy

if sys.version_info >= (3, 11):
    import tomllib as _tomllib
else:
    _tomllib = None

_CRON_TOKEN_RE = re.compile(r"^[0-9*/,\-A-Za-z?]+$")

_LEGACY_CONFIG_ERROR = (
    "legacy Julep configuration detected: `ca.toml` is now `julep.toml`; "
    "`[tool.ca]` is now `[tool.julep]`"
)
_TOP_LEVEL_ALLOWED_KEYS = frozenset(
    {
        "application",
        "agent_round_cap",
        "llm_caller",
        "env",
        "exclude",
        "gates",
        "mcp",
        "pipeline",
        "queue",
        "redaction",
        "schedule",
        "server",
        "src",
        "tags",
    }
)
_GATES_ALLOWED_KEYS = frozenset({"fail_severity"})
_MCP_ALLOWED_KEYS = frozenset({"preflight", "servers"})
_MCP_SERVER_ALLOWED_KEYS = frozenset({"auth", "headers", "url", "version"})
_ENV_ALLOWED_KEYS = frozenset(
    {
        "artifacts",
        "helm_chart",
        "kubernetes_namespace",
        "langfuse_host",
        "payload_encryption_secret",
        "queues",
        "release_store",
        "task_queue",
        "temporal_address",
        "temporal_namespace",
        "vars",
        "worker_context_factory",
        "worker_environment",
        "worker_image",
        "worker_priority_class",
        "worker_secret_environment",
        "worker_service_account",
    }
)
_WORKER_SECRET_ALLOWED_KEYS = frozenset({"key", "secret_name"})
_SCHEDULE_ALLOWED_KEYS = frozenset({"cron", "env", "flow", "input", "paused"})
_PIPELINE_ALLOWED_KEYS = frozenset(
    {"ctx", "lane", "env", "tools", "policy", "context_max_tokens"}
)
# [pipeline.<name>.policy] keys map onto ExecutionPolicy fields (snake_case).
_POLICY_INT_KEYS = frozenset(
    {
        "tool_timeout_s",
        "reasoner_timeout_s",
        "plan_timeout_s",
        "sub_task_timeout_s",
        "agent_task_timeout_s",
        "idempotent_max_attempts",
        "write_max_attempts",
        "reasoner_max_attempts",
        "max_retry_interval_s",
    }
)
_POLICY_FLOAT_KEYS = frozenset({"initial_retry_s", "retry_backoff"})
_POLICY_BOOL_KEYS = frozenset({"trace_content_refs"})
_POLICY_OPTIONAL_INT_KEYS = frozenset({"max_parallel"})
_POLICY_ALLOWED_KEYS = (
    _POLICY_INT_KEYS | _POLICY_FLOAT_KEYS | _POLICY_BOOL_KEYS | _POLICY_OPTIONAL_INT_KEYS
)


@dataclass(frozen=True)
class EnvConfig:
    name: str
    temporal_address: str | None = None
    temporal_namespace: str = 'default'
    task_queue: str = 'julep'
    artifacts: str | None = None
    langfuse_host: str | None = None
    # [env.<name>.vars]: the env profile bound as the dotctx yglu default env
    # inside the resolver/freeze child (never the ambient process environment).
    vars: dict[str, str] = field(default_factory=dict)
    queues: dict[str, str] = field(default_factory=dict)
    release_store: str | None = None
    worker_image: str | None = None
    helm_chart: str = "infra/helm/julep-worker"
    kubernetes_namespace: str = "julep"
    worker_context_factory: str | None = None
    worker_service_account: str | None = None
    worker_priority_class: str | None = None
    payload_encryption_secret: str | None = None
    worker_environment: dict[str, str] = field(default_factory=dict)
    worker_secret_environment: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass(frozen=True)
class ScheduleConfig:
    name: str
    cron: str
    flow: str
    input: Any = None
    env: str = "local"
    paused: bool = False


@dataclass(frozen=True)
class McpServerConfig:
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    auth: str | None = field(default=None, repr=False)
    version: str | None = None


@dataclass(frozen=True)
class JulepConfig:
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
    # Explicit ``module:attribute`` path to a julep.app.Application. This is
    # imported directly; it is never AST-discovered.
    application: str | None = None
    llm_caller: str | None = None
    # Safety ceiling used when a dotctx agent does not declare max_rounds.
    agent_round_cap: int = 32
    pipelines: dict[str, CtxPipelineConfig] = field(default_factory=dict)
    mcp_servers: dict[str, McpServerConfig] = field(default_factory=dict)
    mcp_preflight: str = "pin"

    @property
    def mcp_allowlist(self) -> frozenset[str]:
        return frozenset(server.url for server in self.mcp_servers.values())


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


def _validate_allowed_keys(
    table: object,
    allowed: frozenset[str],
    *,
    context: str,
) -> None:
    if not isinstance(table, dict):
        return
    unknown = sorted(str(key) for key in table if key not in allowed)
    if not unknown:
        return
    key = unknown[0]
    suggestion = get_close_matches(key, sorted(allowed), n=1)
    hint = f"; did you mean {suggestion[0]!r}?" if suggestion else ""
    raise ValueError(f"unknown key {key!r} in {context}{hint}")


def _require_table(value: object, *, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a table")
    return value


def _env_fields(table: object, *, context: str) -> dict[str, str | None]:
    if not isinstance(table, dict):
        return {}
    _validate_allowed_keys(table, _ENV_ALLOWED_KEYS, context=context)
    fields: dict[str, str | None] = {}
    for key in _ENV_ALLOWED_KEYS - {
        "queues",
        "vars",
        "worker_environment",
        "worker_secret_environment",
    }:
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


def _worker_environment(table: object) -> dict[str, str]:
    if not isinstance(table, dict) or not isinstance(table.get("worker_environment"), dict):
        return {}
    return {str(key): str(value) for key, value in table["worker_environment"].items()}


def _worker_secret_environment(
    table: object,
    *,
    context: str,
) -> dict[str, dict[str, str]]:
    if not isinstance(table, dict) or not isinstance(
        table.get("worker_secret_environment"), dict
    ):
        return {}
    result: dict[str, dict[str, str]] = {}
    for name, raw in table["worker_secret_environment"].items():
        if not isinstance(raw, dict) or "secret_name" not in raw or "key" not in raw:
            raise ValueError(
                f"worker_secret_environment.{name} requires secret_name and key"
            )
        _validate_allowed_keys(
            raw,
            _WORKER_SECRET_ALLOWED_KEYS,
            context=f"{context}.worker_secret_environment.{name}",
        )
        result[str(name)] = {
            "secret_name": str(raw["secret_name"]),
            "key": str(raw["key"]),
        }
    return result


def _flow_queues(pyproject_queue: object, julep_toml_queue: object) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in (pyproject_queue, julep_toml_queue):
        if isinstance(raw, dict):
            for key, value in raw.items():
                out[str(key)] = str(value)
    return out


def _build_envs(
    root: Path,
    pyproject_envs: object,
    julep_toml_envs: object,
) -> dict[str, EnvConfig]:
    env_tables: dict[str, dict[str, str | None]] = {}
    env_vars: dict[str, dict[str, str]] = {}
    env_queues: dict[str, dict[str, str]] = {}
    worker_environments: dict[str, dict[str, str]] = {}
    worker_secret_environments: dict[str, dict[str, dict[str, str]]] = {}
    for source, raw_envs in (
        ("[tool.julep.env]", pyproject_envs),
        ("julep.toml [env]", julep_toml_envs),
    ):
        if not isinstance(raw_envs, dict):
            continue
        for name, table in raw_envs.items():
            env_name = str(name)
            context = f"{source}.{env_name}"
            env_tables.setdefault(env_name, {}).update(
                _env_fields(table, context=context)
            )
            # vars merge per-key, julep.toml over pyproject (scalar-field order).
            env_vars.setdefault(env_name, {}).update(_env_vars(table))
            env_queues.setdefault(env_name, {}).update(_env_queues(table))
            worker_environments.setdefault(env_name, {}).update(
                _worker_environment(table)
            )
            worker_secret_environments.setdefault(env_name, {}).update(
                _worker_secret_environment(table, context=context)
            )

    local_defaults: dict[str, str | None] = {
        'artifacts': str(root / '.julep' / 'artifacts'),
        'temporal_address': None,
    }
    env_tables['local'] = {**local_defaults, **env_tables.get('local', {})}

    return {
        name: EnvConfig(
            name=name,
            temporal_address=fields.get('temporal_address'),
            temporal_namespace=fields.get('temporal_namespace') or 'default',
            task_queue=fields.get('task_queue') or 'julep',
            artifacts=fields.get('artifacts'),
            langfuse_host=fields.get('langfuse_host'),
            vars=env_vars.get(name, {}),
            queues=env_queues.get(name, {}),
            release_store=fields.get('release_store'),
            worker_image=fields.get('worker_image'),
            helm_chart=fields.get('helm_chart') or 'infra/helm/julep-worker',
            kubernetes_namespace=fields.get('kubernetes_namespace') or 'julep',
            worker_context_factory=fields.get('worker_context_factory'),
            worker_service_account=fields.get('worker_service_account'),
            worker_priority_class=fields.get('worker_priority_class') or None,
            payload_encryption_secret=fields.get('payload_encryption_secret') or None,
            worker_environment=worker_environments.get(name, {}),
            worker_secret_environment=worker_secret_environments.get(name, {}),
        )
        for name, fields in env_tables.items()
    }


def _build_schedules(
    pyproject_sched: object,
    julep_toml_sched: object,
) -> dict[str, ScheduleConfig]:
    tables: dict[str, dict[str, Any]] = {}
    for raw_schedules in (pyproject_sched, julep_toml_sched):
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
        _validate_allowed_keys(
            table,
            _SCHEDULE_ALLOWED_KEYS,
            context=f"schedule {name!r}",
        )
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


def _build_policy(raw: object, *, context: str) -> ExecutionPolicy | None:
    """Map a ``[pipeline.<name>.policy]`` table onto an ExecutionPolicy."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"{context} policy must be a table")
    _validate_allowed_keys(raw, _POLICY_ALLOWED_KEYS, context=f"{context} policy")
    kwargs: dict[str, Any] = {}
    for raw_key, value in raw.items():
        name = str(raw_key)
        if name in _POLICY_BOOL_KEYS:
            if not isinstance(value, bool):
                raise ValueError(f"{context} policy {name!r} must be a boolean")
            kwargs[name] = value
        elif name in _POLICY_INT_KEYS:
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{context} policy {name!r} must be an integer >= 1")
            kwargs[name] = value
        elif name in _POLICY_FLOAT_KEYS:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"{context} policy {name!r} must be a positive number")
            kwargs[name] = float(value)
        else:  # max_parallel
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 1
            ):
                raise ValueError(f"{context} policy {name!r} must be an integer >= 1 or null")
            kwargs[name] = value
    return ExecutionPolicy(**kwargs)


def _build_pipelines(
    pyproject_pipeline: object,
    julep_toml_pipeline: object,
) -> dict[str, CtxPipelineConfig]:
    tables: dict[str, dict[str, Any]] = {}
    tool_tables: dict[str, dict[str, str]] = {}
    for raw_pipelines in (pyproject_pipeline, julep_toml_pipeline):
        if not isinstance(raw_pipelines, dict):
            continue
        for raw_name, raw_table in raw_pipelines.items():
            name = str(raw_name)
            if not isinstance(raw_table, dict):
                raise ValueError(f"pipeline {name!r} must be a table")
            merged = tables.setdefault(name, {})
            for key, value in raw_table.items():
                if key == "tools":
                    if not isinstance(value, dict):
                        raise ValueError(f"pipeline {name!r} tools must be a table")
                    bound = tool_tables.setdefault(name, {})
                    for raw_alias, raw_ref in value.items():
                        alias = str(raw_alias)
                        if not alias.isidentifier():
                            raise ValueError(
                                f"pipeline {name!r} tool alias {alias!r} must be a "
                                "bare Python identifier"
                            )
                        if not isinstance(raw_ref, str):
                            raise ValueError(
                                f"pipeline {name!r} tool binding {alias!r} must be a string"
                            )
                        server, separator, tool = raw_ref.partition(":")
                        if (
                            separator != ":"
                            or not server
                            or not tool
                            or server.strip() != server
                            or tool.strip() != tool
                            or ":" in tool
                        ):
                            raise ValueError(
                                f"pipeline {name!r} tool binding {alias!r} must use "
                                "'<server>:<tool>'"
                            )
                        bound[alias] = raw_ref
                else:
                    merged[key] = value

    result: dict[str, CtxPipelineConfig] = {}
    for name, table in tables.items():
        context = f"pipeline {name!r}"
        _validate_allowed_keys(table, _PIPELINE_ALLOWED_KEYS, context=context)
        ctx = table.get("ctx")
        if not isinstance(ctx, str) or not ctx or ctx.strip() != ctx:
            raise ValueError(f"{context} requires a non-empty trimmed 'ctx' string")
        lane = table.get("lane", "default")
        if not isinstance(lane, str) or not lane or lane.strip() != lane:
            raise ValueError(f"{context} lane must be a non-empty trimmed string")
        raw_env = table.get("env", {})
        if not isinstance(raw_env, dict):
            raise ValueError(f"{context} env must be a table of string values")
        env: dict[str, str] = {}
        for raw_key, raw_value in raw_env.items():
            if not isinstance(raw_value, str):
                raise ValueError(f"{context} env value {raw_key!r} must be a string")
            env[str(raw_key)] = raw_value
        policy = _build_policy(table.get("policy"), context=context)
        context_max_tokens = table.get("context_max_tokens")
        if context_max_tokens is not None and (
            isinstance(context_max_tokens, bool)
            or not isinstance(context_max_tokens, int)
            or context_max_tokens < 1
        ):
            raise ValueError(
                f"{context} context_max_tokens must be a positive integer"
            )
        result[name] = CtxPipelineConfig(
            name=name,
            ctx=ctx,
            lane=lane,
            env=env,
            tools=tool_tables.get(name, {}),
            policy=policy,
            context_max_tokens=context_max_tokens,
        )
    return result


def _mcp_table(table: object, *, context: str) -> dict[str, Any]:
    parsed = _require_table(table, context=context)
    _validate_allowed_keys(parsed, _MCP_ALLOWED_KEYS, context=context)
    return parsed


def _mcp_headers(table: object, *, context: str) -> dict[str, str]:
    parsed = _require_table(table, context=context)
    headers: dict[str, str] = {}
    for raw_name, raw_value in parsed.items():
        name = str(raw_name)
        if not name or name.strip() != name:
            raise ValueError(f"header names in {context} must be non-empty and trimmed")
        if not isinstance(raw_value, str):
            raise ValueError(f"header {name!r} in {context} must be a string")
        headers[name] = raw_value
    return headers


def _build_mcp_servers(
    pyproject_mcp: object,
    julep_toml_mcp: object,
) -> dict[str, McpServerConfig]:
    tables: dict[str, dict[str, Any]] = {}
    headers: dict[str, dict[str, str]] = {}
    for source, raw_mcp in (
        ("[tool.julep.mcp]", pyproject_mcp),
        ("julep.toml [mcp]", julep_toml_mcp),
    ):
        mcp = _mcp_table(raw_mcp, context=source)
        raw_servers = _require_table(mcp.get("servers", {}), context=f"{source}.servers")
        for raw_name, raw_server in raw_servers.items():
            name = str(raw_name)
            if not name or name.strip() != name:
                raise ValueError(f"MCP server ids in {source}.servers must be non-empty and trimmed")
            context = f"{source}.servers.{name}"
            server = _require_table(raw_server, context=context)
            _validate_allowed_keys(server, _MCP_SERVER_ALLOWED_KEYS, context=context)
            merged = tables.setdefault(name, {})
            for key, value in server.items():
                if key == "headers":
                    headers.setdefault(name, {}).update(
                        _mcp_headers(value, context=f"{context}.headers")
                    )
                else:
                    merged[key] = value

    result: dict[str, McpServerConfig] = {}
    for name, table in tables.items():
        context = f"MCP server {name!r}"
        url = table.get("url")
        if not isinstance(url, str) or not url or url.strip() != url:
            raise ValueError(f"{context} requires a non-empty trimmed 'url' string")
        try:
            parsed_url = urlsplit(url)
            hostname = parsed_url.hostname
        except ValueError:
            parsed_url = None
            hostname = None
        if (
            parsed_url is None
            or parsed_url.scheme not in {"http", "https"}
            or hostname is None
            or parsed_url.fragment
        ):
            raise ValueError(f"{context} url must be an absolute http(s) URL")
        if parsed_url.username is not None or parsed_url.password is not None:
            raise ValueError(f"{context} url must not contain credentials; use auth or headers")
        auth = table.get("auth")
        if auth is not None and (
            not isinstance(auth, str) or not auth or auth.strip() != auth
        ):
            raise ValueError(f"{context} auth must be a non-empty trimmed string")
        version = table.get("version")
        if version is not None and (
            not isinstance(version, str) or not version or version.strip() != version
        ):
            raise ValueError(f"{context} version must be a non-empty trimmed string")
        result[name] = McpServerConfig(
            url=url,
            headers=headers.get(name, {}),
            auth=auth,
            version=version,
        )
    return result


def _build_mcp_preflight(pyproject_mcp: object, julep_toml_mcp: object) -> str:
    policy: object = "pin"
    for source, raw_mcp in (
        ("[tool.julep.mcp]", pyproject_mcp),
        ("julep.toml [mcp]", julep_toml_mcp),
    ):
        mcp = _mcp_table(raw_mcp, context=source)
        if "preflight" in mcp:
            policy = mcp["preflight"]
    if not isinstance(policy, str) or policy not in {"pin", "names", "off"}:
        raise ValueError("MCP preflight must be one of 'pin', 'names', or 'off'")
    return policy


def load_config(root: str | Path) -> JulepConfig:
    """Read ``[tool.julep]``, then overlay a sibling ``julep.toml``."""
    root = Path(root).resolve()
    legacy_config = root / "ca.toml"
    if legacy_config.exists():
        raise ValueError(_LEGACY_CONFIG_ERROR)

    pyproject_data = _read_toml(root / "pyproject.toml")
    tool = _require_table(pyproject_data.get("tool", {}), context="[tool]")
    if "ca" in tool:
        raise ValueError(_LEGACY_CONFIG_ERROR)

    pyproject = _require_table(tool.get("julep", {}), context="[tool.julep]")
    julep_toml = _read_toml(root / "julep.toml")
    _validate_allowed_keys(pyproject, _TOP_LEVEL_ALLOWED_KEYS, context="[tool.julep]")
    _validate_allowed_keys(julep_toml, _TOP_LEVEL_ALLOWED_KEYS, context="julep.toml")

    pyproject_gates = _require_table(
        pyproject.get("gates", {}),
        context="[tool.julep.gates]",
    )
    julep_toml_gates = _require_table(
        julep_toml.get("gates", {}),
        context="julep.toml [gates]",
    )
    _validate_allowed_keys(
        pyproject_gates,
        _GATES_ALLOWED_KEYS,
        context="[tool.julep.gates]",
    )
    _validate_allowed_keys(
        julep_toml_gates,
        _GATES_ALLOWED_KEYS,
        context="julep.toml [gates]",
    )
    mcp_servers = _build_mcp_servers(
        pyproject.get("mcp", {}),
        julep_toml.get("mcp", {}),
    )
    mcp_preflight = _build_mcp_preflight(
        pyproject.get("mcp", {}),
        julep_toml.get("mcp", {}),
    )

    merged: dict[str, Any] = {**pyproject, **julep_toml}
    agent_round_cap = merged.get("agent_round_cap", 32)
    if (
        not isinstance(agent_round_cap, int)
        or isinstance(agent_round_cap, bool)
        or agent_round_cap < 1
    ):
        raise ValueError("agent_round_cap must be an integer >= 1")
    gates = {**pyproject_gates, **julep_toml_gates}
    return JulepConfig(
        root=root,
        src=list(merged.get('src', [str(root)])),
        exclude=list(merged.get('exclude', [])),
        tags={k: list(v) for k, v in merged.get('tags', {}).items()},
        flow_queues=_flow_queues(pyproject.get('queue', {}), julep_toml.get('queue', {})),
        fail_severity=str(gates.get('fail_severity', 'error')),
        envs=_build_envs(root, pyproject.get('env', {}), julep_toml.get('env', {})),
        schedules=_build_schedules(
            pyproject.get("schedule", {}),
            julep_toml.get("schedule", {}),
        ),
        application=(str(merged["application"]) if merged.get("application") else None),
        llm_caller=(str(merged["llm_caller"]) if merged.get("llm_caller") else None),
        agent_round_cap=agent_round_cap,
        pipelines=_build_pipelines(
            pyproject.get("pipeline", {}),
            julep_toml.get("pipeline", {}),
        ),
        mcp_servers=mcp_servers,
        mcp_preflight=mcp_preflight,
    )
