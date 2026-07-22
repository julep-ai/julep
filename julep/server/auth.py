"""Static bearer-key authentication for the control-plane API."""

from __future__ import annotations

import hmac
from importlib import import_module
import os
import re
import signal
from dataclasses import dataclass, field
from types import FrameType
from typing import TYPE_CHECKING, Any, Callable, Iterable, Literal, Mapping, Optional, Protocol, Sequence, cast

if TYPE_CHECKING:
    from .settings import ServerSettings


class _RequestApp(Protocol):
    state: Any


if TYPE_CHECKING:

    class Request(Protocol):
        headers: Mapping[str, str]
        app: _RequestApp

else:
    try:
        Request = import_module("starlette.requests").Request
    except ModuleNotFoundError:
        # The annotation is resolved by FastAPI only when the optional server
        # dependencies are installed.  Keeping this fallback makes auth/config
        # importable from the core package without Starlette.
        Request = object


_KEY_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
ReloadSource = Callable[[], Iterable["ApiKey"]]


@dataclass(frozen=True)
class ApiKey:
    """One static API credential and the identity fields it owns."""

    name: str
    token: str = field(repr=False)
    principal_base: dict[str, Any] = field(default_factory=dict)
    admin: bool = False
    role: Literal["client", "worker", "admin"] = "client"

    def __post_init__(self) -> None:
        if _KEY_NAME.fullmatch(self.name) is None:
            raise ValueError(
                "API key names must contain only letters, numbers, '.', '_', or '-'"
            )
        if not self.token:
            raise ValueError(f"API key {self.name!r} has an empty token")
        if self.role not in {"client", "worker", "admin"}:
            raise ValueError(f"API key {self.name!r} has invalid role {self.role!r}")
        if self.admin and self.role == "worker":
            raise ValueError("an API key cannot be both worker and admin")
        effective_role: Literal["client", "worker", "admin"] = (
            "admin" if self.admin else self.role
        )
        object.__setattr__(self, "role", effective_role)
        object.__setattr__(self, "admin", effective_role == "admin")
        principal = self.principal_base or {"key": self.name}
        object.__setattr__(self, "principal_base", dict(principal))


def parse_api_keys(raw: object) -> tuple[ApiKey, ...]:
    """Parse ``name:token[:client|worker|admin]`` static credentials."""

    if raw is None or raw == "":
        return ()
    chunks: list[str] = []
    if isinstance(raw, str):
        chunks.extend(part for part in re.split(r"[\s,]+", raw.strip()) if part)
    elif isinstance(raw, Sequence):
        for item in raw:
            if not isinstance(item, str):
                raise ValueError("API key entries must be strings")
            chunks.extend(part for part in re.split(r"[\s,]+", item.strip()) if part)
    else:
        raise ValueError("JULEP_API_KEYS must be a string or list of strings")

    keys: list[ApiKey] = []
    names: set[str] = set()
    tokens: set[str] = set()
    for entry in chunks:
        parts = entry.split(":")
        if len(parts) not in (2, 3) or not parts[0] or not parts[1]:
            raise ValueError(
                "JULEP_API_KEYS entries must use "
                "name:token[:client|worker|admin]"
            )
        role = "client" if len(parts) == 2 else parts[2].lower()
        if role not in {"client", "worker", "admin"}:
            raise ValueError(
                "the optional third JULEP_API_KEYS field must be one of "
                "'client', 'worker', or 'admin'"
            )
        name, token = parts[0], parts[1]
        if name in names:
            raise ValueError(f"duplicate API key name {name!r}")
        if token in tokens:
            raise ValueError("duplicate API key tokens are not allowed")
        names.add(name)
        tokens.add(token)
        keys.append(
            ApiKey(
                name=name,
                token=token,
                principal_base={"key": name},
                role=cast(Literal["client", "worker", "admin"], role),
            )
        )
    return tuple(keys)


class KeyRing:
    """Reloadable static key collection with constant-time token comparison."""

    def __init__(
        self,
        keys: Iterable[ApiKey],
        *,
        reload_source: Optional[ReloadSource] = None,
    ) -> None:
        self._keys = tuple(keys)
        self._reload_source = reload_source
        self._previous_sighup_handler: Any = None

    @classmethod
    def from_settings(cls, settings: ServerSettings) -> "KeyRing":
        """Create a ring whose reload observes current project config and environment."""

        from .settings import ServerSettings

        def source() -> tuple[ApiKey, ...]:
            return ServerSettings.from_env(root=settings.config_root).api_keys

        return cls(settings.api_keys, reload_source=source)

    @property
    def keys(self) -> tuple[ApiKey, ...]:
        """A token-redacting snapshot, primarily useful for diagnostics/tests."""

        return self._keys

    def authenticate(self, bearer: Optional[str]) -> Optional[ApiKey]:
        """Return the matching key after comparing the candidate with every token."""

        candidate = "" if bearer is None else bearer
        found: Optional[ApiKey] = None
        for key in self._keys:
            matches = hmac.compare_digest(candidate, key.token)
            if matches and found is None:
                found = key
        return found

    def reload(self) -> None:
        """Atomically replace keys from the configured source or current environment."""

        if self._reload_source is None:
            keys = parse_api_keys(os.environ.get("JULEP_API_KEYS", ""))
        else:
            keys = tuple(self._reload_source())
        self._keys = tuple(keys)

    def install_sighup_handler(self) -> bool:
        """Reload on SIGHUP when signals are available in the current thread."""

        sighup = getattr(signal, "SIGHUP", None)
        if sighup is None:
            return False
        try:
            self._previous_sighup_handler = signal.getsignal(sighup)
            signal.signal(sighup, self._handle_sighup)
        except (OSError, ValueError):
            self._previous_sighup_handler = None
            return False
        return True

    def restore_sighup_handler(self) -> None:
        """Restore the handler replaced by :meth:`install_sighup_handler`."""

        sighup = getattr(signal, "SIGHUP", None)
        previous = self._previous_sighup_handler
        if sighup is None or previous is None:
            return
        try:
            signal.signal(sighup, previous)
        except (OSError, ValueError):
            pass
        self._previous_sighup_handler = None

    def _handle_sighup(self, _signum: int, _frame: Optional[FrameType]) -> None:
        self.reload()


def _unauthorized() -> Exception:
    http_exception = import_module("fastapi").HTTPException
    return cast(
        Exception,
        http_exception(
            status_code=401,
            detail="missing or invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        ),
    )


def _forbidden(detail: str, *, status_code: int) -> Exception:
    http_exception = import_module("fastapi").HTTPException
    return cast(Exception, http_exception(status_code=status_code, detail=detail))


def require_key(request: Request) -> ApiKey:
    """FastAPI dependency requiring a valid ``Authorization: Bearer`` key."""

    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise _unauthorized()
    keyring = getattr(request.app.state, "keyring", None)
    if not isinstance(keyring, KeyRing):
        raise RuntimeError("server keyring is not configured")
    key = keyring.authenticate(token.strip())
    if key is None:
        raise _unauthorized()
    return key


def require_admin(request: Request) -> ApiKey:
    """FastAPI dependency requiring a valid admin key."""

    key = require_key(request)
    if key.role != "admin":
        raise _forbidden("admin API key required", status_code=403)
    return key


def require_worker(request: Request) -> ApiKey:
    """FastAPI dependency requiring a worker-only credential."""

    key = require_key(request)
    if key.role != "worker":
        raise _forbidden("worker API key required", status_code=403)
    return key


def require_client(request: Request) -> ApiKey:
    """Require a client/admin key, explicitly excluding worker credentials."""

    key = require_key(request)
    if key.role == "worker":
        raise _forbidden("worker API keys cannot access this route", status_code=403)
    return key


def merge_principal(key: ApiKey, requested: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Merge request metadata without allowing key-owned identity overrides."""

    effective = dict(key.principal_base)
    if requested is None:
        return effective
    for field_name, value in requested.items():
        if field_name in key.principal_base and key.principal_base[field_name] != value:
            raise _forbidden(
                f"principal field {field_name!r} is owned by the API key",
                status_code=400,
            )
        effective[field_name] = value
    return effective


def owner_scoped(key: ApiKey, run_row: Mapping[str, Any]) -> bool:
    """Whether a key may read a run; admins intentionally bypass owner scoping."""

    if key.admin:
        return True
    principal = run_row.get("principal")
    if not isinstance(principal, Mapping):
        return False
    return all(
        name in principal and principal[name] == value
        for name, value in key.principal_base.items()
    )


__all__ = [
    "ApiKey",
    "KeyRing",
    "merge_principal",
    "owner_scoped",
    "parse_api_keys",
    "require_admin",
    "require_client",
    "require_key",
    "require_worker",
]
