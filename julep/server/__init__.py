"""Optional FastAPI control-plane primitives."""

from typing import TYPE_CHECKING, Any

from .auth import (
    ApiKey,
    KeyRing,
    merge_principal,
    owner_scoped,
    require_admin,
    require_client,
    require_key,
    require_worker,
)
from .settings import ServerSettings
from .temporal import TemporalClientGateway, TemporalGateway, create_temporal_gateway

if TYPE_CHECKING:
    from .local import LocalExecutionGateway, create_local_app


def __getattr__(name: str) -> Any:
    if name in {"LocalExecutionGateway", "create_local_app"}:
        from . import local

        return getattr(local, name)
    raise AttributeError(name)

__all__ = [
    "ApiKey",
    "KeyRing",
    "LocalExecutionGateway",
    "ServerSettings",
    "TemporalClientGateway",
    "TemporalGateway",
    "create_temporal_gateway",
    "create_local_app",
    "merge_principal",
    "owner_scoped",
    "require_admin",
    "require_client",
    "require_key",
    "require_worker",
]
