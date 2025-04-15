import asyncio

from fastapi import HTTPException

from ...common.utils.checks import (
    check_integration_service,
    check_litellm,
    check_postgres,
    check_temporal,
)
from .router import router


@router.get("/healthz", tags=["healthz"])
async def check_health() -> dict:
    # Run all health checks concurrently
    postgres_status, temporal_status, litellm_status, integration_status = await asyncio.gather(
        check_postgres(),
        check_temporal(),
        check_litellm(),
        check_integration_service(),
    )

    # Create health status with results
    services = {
        "postgres": postgres_status,
        "temporal": temporal_status,
        "litellm": litellm_status,
        "integration_service": integration_status,
    }

    # If any service is down, mark overall status as degraded
    if any(status == "error" for status in services.values()):
        raise HTTPException(status_code=500, detail=services)

    return services
