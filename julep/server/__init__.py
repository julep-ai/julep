"""Optional FastAPI control-plane primitives."""

from .auth import (
    ApiKey,
    KeyRing,
    merge_principal,
    owner_scoped,
    require_admin,
    require_key,
)
from .settings import ServerSettings
from .temporal import TemporalClientGateway, TemporalGateway, create_temporal_gateway

__all__ = [
    "ApiKey",
    "KeyRing",
    "ServerSettings",
    "TemporalClientGateway",
    "TemporalGateway",
    "create_temporal_gateway",
    "merge_principal",
    "owner_scoped",
    "require_admin",
    "require_key",
]
