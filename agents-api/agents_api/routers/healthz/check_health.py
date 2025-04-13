import asyncio
import logging
from uuid import UUID

from fastapi import HTTPException
from httpx import AsyncClient

from ...clients import litellm
from ...clients.temporal import get_client
from ...env import integration_service_url
from ...queries.agents.list_agents import list_agents as list_agents_query
from .router import router


@router.get("/healthz", tags=["healthz"])
async def check_health() -> dict:
    health_status = {
        "status": "ok",
        "services": {
            "postgres": "ok",
            "temporal": "ok",
            "litellm": "ok",
            "integration_service": "ok",
        },
    }

    async def check_postgres():
        try:
            await list_agents_query(
                developer_id=UUID("00000000-0000-0000-0000-000000000000"),
            )
            return "ok"
        except Exception as e:
            logging.error("Postgres health check failed: %s", str(e))
            return "error"

    async def check_temporal():
        try:
            client = await get_client()
            client.get_workflow_handle("non-existent-workflow-id")
            return "ok"
        except Exception as e:
            logging.error("Temporal health check failed: %s", str(e))
            return "error"

    async def check_litellm():
        try:
            await litellm.get_model_list()
            return "ok"
        except Exception as e:
            logging.error("LiteLLM health check failed: %s", str(e))
            return "error"

    async def check_integration_service():
        try:
            async with AsyncClient(timeout=60) as client:
                response = await client.get(
                    f"{integration_service_url}/integrations",
                )
                response.raise_for_status()
            return "ok"
        except Exception as e:
            logging.error("Integration service health check failed: %s", str(e))
            return "error"

    # Run all health checks concurrently
    postgres_status, temporal_status, litellm_status, integration_status = await asyncio.gather(
        check_postgres(),
        check_temporal(),
        check_litellm(),
        check_integration_service(),
    )

    # Update health status with results
    health_status["services"]["postgres"] = postgres_status
    health_status["services"]["temporal"] = temporal_status
    health_status["services"]["litellm"] = litellm_status
    health_status["services"]["integration_service"] = integration_status

    # If any service is down, mark overall status as degraded
    if any(status == "error" for status in health_status["services"].values()):
        health_status["status"] = "degraded"
        raise HTTPException(status_code=500, detail=health_status)

    return health_status
