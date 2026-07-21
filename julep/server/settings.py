"""Configuration for the optional Julep control-plane server.

This module deliberately imports neither FastAPI, psycopg, nor Temporal at
module import time.  The CLI can therefore discover its commands without
making the ``server`` extra a dependency of the core package.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional

from ..execution.serve import payload_encryption_from_env

if sys.version_info >= (3, 11):
    import tomllib as _tomllib
else:
    _tomllib = None

if TYPE_CHECKING:
    from ..app_deploy import LaneReconciler
    from ..cas import CASStore
    from ..execution.projection_store import ExecutionStore
    from .auth import ApiKey
    from .temporal import TemporalGateway


_TRUE = frozenset({"1", "true", "yes", "on"})
_FALSE = frozenset({"0", "false", "no", "off"})


def _read_toml(path: Path) -> dict[str, Any]:
    if _tomllib is None or not path.is_file():
        return {}
    try:
        with path.open("rb") as handle:
            data = _tomllib.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_server_config(root: Path) -> dict[str, Any]:
    """Read pyproject settings, then overlay the sibling ``julep.toml``."""

    pyproject = _read_toml(root / "pyproject.toml")
    py_server: object = pyproject
    for key in ("tool", "julep", "server"):
        py_server = py_server.get(key, {}) if isinstance(py_server, dict) else {}

    julep_toml = _read_toml(root / "julep.toml")
    local_server = julep_toml.get("server", {})
    return {
        **(py_server if isinstance(py_server, dict) else {}),
        **(local_server if isinstance(local_server, dict) else {}),
    }


def _value(
    env: Mapping[str, str],
    env_name: str,
    config: Mapping[str, Any],
    config_name: str,
    default: Any = None,
) -> Any:
    if env_name in env:
        return env[env_name]
    return config.get(config_name, default)


def _optional_text(value: Any, *, name: str) -> Optional[str]:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    stripped = value.strip()
    if not stripped:
        return None
    return stripped


def _text(value: Any, *, name: str) -> str:
    parsed = _optional_text(value, name=name)
    if parsed is None:
        raise ValueError(f"{name} must be a non-empty string")
    return parsed


def _bool(value: Any, *, name: str, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE:
            return True
        if lowered in _FALSE:
            return False
    raise ValueError(f"{name} must be a boolean (true/false), got {value!r}")


def _int(value: Any, *, name: str, default: int, minimum: int = 1) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer, got {value!r}")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc
    if parsed < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {parsed}")
    return parsed


def _float(value: Any, *, name: str, default: float, minimum: float = 0.0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number, got {value!r}")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number, got {value!r}") from exc
    if parsed < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {parsed}")
    return parsed


def _string_map(value: Any, *, name: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a table")
    result: dict[str, str] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key).strip()
        if not key or not isinstance(raw_value, str) or not raw_value.strip():
            raise ValueError(f"{name} keys and values must be non-empty strings")
        result[key] = raw_value.strip()
    return result


def _json_object(value: str, *, name: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"{name} must be a JSON object") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object")
    return parsed


def _config_or_json_object(
    env: Mapping[str, str],
    env_name: str,
    config: Mapping[str, Any],
    config_name: str,
) -> Any:
    if env_name in env:
        return _json_object(env[env_name], name=env_name)
    return config.get(config_name)


def _secret_environment_map(value: Any, *, name: str) -> dict[str, dict[str, str]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a table")
    result: dict[str, dict[str, str]] = {}
    for raw_name, raw_source in value.items():
        environment_name = str(raw_name).strip()
        if not environment_name or not isinstance(raw_source, dict):
            raise ValueError(
                f"{name} values must contain non-empty secret_name and key strings"
            )
        secret_name = raw_source.get("secret_name")
        key = raw_source.get("key")
        if (
            not isinstance(secret_name, str)
            or not secret_name.strip()
            or not isinstance(key, str)
            or not key.strip()
        ):
            raise ValueError(
                f"{name} values must contain non-empty secret_name and key strings"
            )
        result[environment_name] = {
            "secret_name": secret_name.strip(),
            "key": key.strip(),
        }
    return result


def _payload_environment(
    env: Mapping[str, str], config: Mapping[str, Any]
) -> dict[str, str]:
    effective: dict[str, str] = {}
    config_keys = {
        "TEMPORAL_PAYLOAD_KEYS": ("temporal_payload_keys", "payload_keys"),
        "TEMPORAL_PAYLOAD_KEY_ID": ("temporal_payload_key_id", "payload_key_id"),
        "TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED": (
            "temporal_payload_encryption_required",
            "payload_encryption_required",
        ),
    }
    for env_name, aliases in config_keys.items():
        for alias in aliases:
            if alias not in config:
                continue
            value = config[alias]
            if isinstance(value, bool):
                effective[env_name] = "true" if value else "false"
            elif value is not None:
                effective[env_name] = str(value)
            break
        if env_name in env:
            effective[env_name] = env[env_name]
    # Control-plane workflow starts are encrypted by default. Operators of an
    # explicitly trusted plaintext Temporal deployment must opt out.
    effective.setdefault("TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED", "true")
    return effective


@dataclass(frozen=True)
class ServerSettings:
    """Environment-shaped configuration for the FastAPI control plane.

    Environment variables override ``[tool.julep.server]`` in
    ``pyproject.toml`` and ``[server]`` in ``julep.toml``.  The latter overlays
    the former, matching the authoring CLI's configuration precedence.
    """

    api_keys: tuple[ApiKey, ...] = ()
    execution_store_dsn: Optional[str] = field(default=None, repr=False)
    cas_url: str = "file:///.julep/cas"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "julep"
    temporal_api_key: Optional[str] = field(default=None, repr=False)
    temporal_tls: bool = False
    payload_keys: Optional[str] = field(default=None, repr=False)
    payload_key_id: Optional[str] = None
    payload_encryption_required: bool = True
    host: str = "127.0.0.1"
    port: int = 8080
    projection_batch_size: int = 20
    projection_batch_interval_s: float = 2.0
    reconcile_interval_s: float = 60.0
    helm_chart: Optional[str] = None
    kubernetes_namespace: str = "julep"
    worker_context_factory: Optional[str] = None
    worker_application: Optional[str] = None
    worker_runtime_declarations_hash: Optional[str] = None
    worker_environment: dict[str, str] = field(default_factory=dict)
    worker_secret_environment: dict[str, dict[str, str]] = field(default_factory=dict)
    payload_encryption_secret: Optional[str] = None
    worker_service_account: Optional[str] = None
    worker_priority_class: Optional[str] = None
    queue_by_lane: dict[str, str] = field(default_factory=dict)
    config_root: Path = field(default_factory=Path.cwd, repr=False, compare=False)

    @classmethod
    def from_env(
        cls,
        env: Optional[Mapping[str, str]] = None,
        *,
        root: Optional[str | Path] = None,
    ) -> "ServerSettings":
        """Build settings from project files and an environment mapping."""

        from .auth import parse_api_keys

        source: Mapping[str, str] = os.environ if env is None else env
        config_root = Path.cwd() if root is None else Path(root)
        config_root = config_root.resolve()
        config = _read_server_config(config_root)

        raw_api_keys = _value(source, "JULEP_API_KEYS", config, "api_keys", "")
        api_keys = parse_api_keys(raw_api_keys)
        temporal_api_key = _optional_text(
            _value(source, "TEMPORAL_API_KEY", config, "temporal_api_key"),
            name="TEMPORAL_API_KEY",
        )
        payload_keys, payload_key_id, payload_required = payload_encryption_from_env(
            _payload_environment(source, config)
        )
        cas_default = (config_root / ".julep" / "cas").resolve().as_uri()
        port = _int(
            _value(source, "JULEP_SERVER_PORT", config, "port", 8080),
            name="JULEP_SERVER_PORT",
            default=8080,
        )
        if port > 65535:
            raise ValueError(f"JULEP_SERVER_PORT must be at most 65535, got {port}")

        return cls(
            api_keys=api_keys,
            execution_store_dsn=_optional_text(
                _value(
                    source,
                    "JULEP_EXECUTION_STORE_DSN",
                    config,
                    "execution_store_dsn",
                ),
                name="JULEP_EXECUTION_STORE_DSN",
            ),
            cas_url=_text(
                _value(source, "JULEP_CAS_URL", config, "cas_url", cas_default),
                name="JULEP_CAS_URL",
            ),
            temporal_address=_text(
                _value(
                    source,
                    "TEMPORAL_ADDRESS",
                    config,
                    "temporal_address",
                    "localhost:7233",
                ),
                name="TEMPORAL_ADDRESS",
            ),
            temporal_namespace=_text(
                _value(
                    source,
                    "TEMPORAL_NAMESPACE",
                    config,
                    "temporal_namespace",
                    "default",
                ),
                name="TEMPORAL_NAMESPACE",
            ),
            temporal_task_queue=_text(
                _value(
                    source,
                    "TEMPORAL_TASK_QUEUE",
                    config,
                    "temporal_task_queue",
                    "julep",
                ),
                name="TEMPORAL_TASK_QUEUE",
            ),
            temporal_api_key=temporal_api_key,
            temporal_tls=_bool(
                _value(source, "TEMPORAL_TLS", config, "temporal_tls"),
                name="TEMPORAL_TLS",
                default=temporal_api_key is not None,
            ),
            payload_keys=payload_keys,
            payload_key_id=payload_key_id,
            payload_encryption_required=payload_required,
            host=_text(
                _value(source, "JULEP_SERVER_HOST", config, "host", "127.0.0.1"),
                name="JULEP_SERVER_HOST",
            ),
            port=port,
            projection_batch_size=_int(
                _value(
                    source,
                    "JULEP_PROJECTION_BATCH_SIZE",
                    config,
                    "projection_batch_size",
                    20,
                ),
                name="JULEP_PROJECTION_BATCH_SIZE",
                default=20,
            ),
            projection_batch_interval_s=_float(
                _value(
                    source,
                    "JULEP_PROJECTION_BATCH_INTERVAL_S",
                    config,
                    "projection_batch_interval_s",
                    2.0,
                ),
                name="JULEP_PROJECTION_BATCH_INTERVAL_S",
                default=2.0,
            ),
            reconcile_interval_s=_float(
                _value(
                    source,
                    "JULEP_SERVER_RECONCILE_INTERVAL_S",
                    config,
                    "reconcile_interval_s",
                    60.0,
                ),
                name="JULEP_SERVER_RECONCILE_INTERVAL_S",
                default=60.0,
            ),
            helm_chart=_optional_text(
                _value(source, "JULEP_SERVER_HELM_CHART", config, "helm_chart"),
                name="JULEP_SERVER_HELM_CHART",
            ),
            kubernetes_namespace=_text(
                _value(
                    source,
                    "JULEP_SERVER_KUBERNETES_NAMESPACE",
                    config,
                    "kubernetes_namespace",
                    "julep",
                ),
                name="JULEP_SERVER_KUBERNETES_NAMESPACE",
            ),
            worker_context_factory=_optional_text(
                _value(
                    source,
                    "JULEP_SERVER_WORKER_CONTEXT_FACTORY",
                    config,
                    "worker_context_factory",
                ),
                name="JULEP_SERVER_WORKER_CONTEXT_FACTORY",
            ),
            worker_application=_optional_text(
                _value(
                    source,
                    "JULEP_SERVER_WORKER_APPLICATION",
                    config,
                    "worker_application",
                ),
                name="JULEP_SERVER_WORKER_APPLICATION",
            ),
            worker_runtime_declarations_hash=_optional_text(
                _value(
                    source,
                    "JULEP_SERVER_WORKER_RUNTIME_DECLARATIONS_HASH",
                    config,
                    "worker_runtime_declarations_hash",
                ),
                name="JULEP_SERVER_WORKER_RUNTIME_DECLARATIONS_HASH",
            ),
            worker_environment=_string_map(
                _config_or_json_object(
                    source,
                    "JULEP_SERVER_WORKER_ENVIRONMENT",
                    config,
                    "worker_environment",
                ),
                name="worker_environment",
            ),
            worker_secret_environment=_secret_environment_map(
                _config_or_json_object(
                    source,
                    "JULEP_SERVER_WORKER_SECRET_ENVIRONMENT",
                    config,
                    "worker_secret_environment",
                ),
                name="worker_secret_environment",
            ),
            payload_encryption_secret=_optional_text(
                _value(
                    source,
                    "JULEP_SERVER_PAYLOAD_ENCRYPTION_SECRET",
                    config,
                    "payload_encryption_secret",
                ),
                name="JULEP_SERVER_PAYLOAD_ENCRYPTION_SECRET",
            ),
            worker_service_account=_optional_text(
                _value(
                    source,
                    "JULEP_SERVER_WORKER_SERVICE_ACCOUNT",
                    config,
                    "worker_service_account",
                ),
                name="JULEP_SERVER_WORKER_SERVICE_ACCOUNT",
            ),
            worker_priority_class=_optional_text(
                _value(
                    source,
                    "JULEP_SERVER_WORKER_PRIORITY_CLASS",
                    config,
                    "worker_priority_class",
                ),
                name="JULEP_SERVER_WORKER_PRIORITY_CLASS",
            ),
            queue_by_lane=_string_map(config.get("queue_by_lane"), name="queue_by_lane"),
            config_root=config_root,
        )

    def build_store(self) -> ExecutionStore:
        """Construct the Postgres execution store, failing clearly if unconfigured."""

        if self.execution_store_dsn is None:
            raise ValueError(
                "JULEP_EXECUTION_STORE_DSN is required to serve the API; "
                "set it to a PostgreSQL connection string"
            )
        from ..execution.projection_store import PostgresExecutionStore

        return PostgresExecutionStore(self.execution_store_dsn)

    def build_cas(self) -> CASStore:
        """Construct the configured release/blob content-addressed store."""

        from ..cas import cas_from_url

        return cas_from_url(self.cas_url)

    async def build_gateway(self) -> TemporalGateway:
        """Connect a real Temporal gateway lazily."""

        from .temporal import create_temporal_gateway

        return await create_temporal_gateway(self)

    def build_reconciler(self) -> Optional[LaneReconciler]:
        """Build the optional Helm reconciler when a chart is configured."""

        if self.helm_chart is None:
            return None
        if self.worker_context_factory is None or self.payload_encryption_secret is None:
            raise ValueError(
                "Helm reconciliation requires JULEP_SERVER_WORKER_CONTEXT_FACTORY "
                "and JULEP_SERVER_PAYLOAD_ENCRYPTION_SECRET"
            )
        from ..app_deploy import HelmLaneReconciler

        return HelmLaneReconciler(
            chart=self.helm_chart,
            namespace=self.kubernetes_namespace,
            temporal_address=self.temporal_address,
            temporal_namespace=self.temporal_namespace,
            worker_context_factory=self.worker_context_factory,
            worker_application=self.worker_application,
            worker_runtime_declarations_hash=self.worker_runtime_declarations_hash,
            worker_environment=self.worker_environment,
            worker_secret_environment=self.worker_secret_environment,
            payload_encryption_secret=self.payload_encryption_secret,
            worker_service_account=self.worker_service_account,
            worker_priority_class=self.worker_priority_class,
        )


__all__ = ["ServerSettings"]
