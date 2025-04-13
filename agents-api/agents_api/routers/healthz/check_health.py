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

    # Check TimescaleDB connection
    try:
        await list_agents_query(
            developer_id=UUID("00000000-0000-0000-0000-000000000000"),
        )
    except Exception as e:
        logging.error("Postgres health check failed: %s", str(e))
        health_status["services"]["postgres"] = "error"
        health_status["status"] = "degraded"

    # Check Temporal connection
    try:
        # Use the existing pattern to get the temporal client
        # This checks if the connection can be established
        client = await get_client()
        # Get system info to verify the connection is working
        client.get_workflow_handle("non-existent-workflow-id")
    except Exception as e:
        logging.error("Temporal health check failed: %s", str(e))
        health_status["services"]["temporal"] = "error"
        health_status["status"] = "degraded"

    # Check LiteLLM connection
    try:
        # Use the get_model_list function to validate connectivity
        await litellm.get_model_list()
    except Exception as e:
        logging.error("LiteLLM health check failed: %s", str(e))
        health_status["services"]["litellm"] = "error"
        health_status["status"] = "degraded"

    # Check integration service connection
    try:
        async with AsyncClient(timeout=600) as client:
            response = await client.get(
                f"{integration_service_url}/integrations",
            )
            response.raise_for_status()
    except Exception as e:
        logging.error("Integration service health check failed: %s", str(e))
        health_status["services"]["integration_service"] = "error"
        health_status["status"] = "degraded"

    # If any service is down, return 500 status code
    if health_status["status"] != "ok":
        raise HTTPException(status_code=500, detail=health_status)

    return health_status
