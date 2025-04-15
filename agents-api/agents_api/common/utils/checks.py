import logging
from typing import Literal
from uuid import UUID

from httpx import AsyncClient

from ...clients import litellm
from ...clients.temporal import get_client
from ...env import integration_service_url
from ...queries.agents.list_agents import list_agents as list_agents_query

HealthStatus = Literal["ok", "error"]
ServiceHealth = dict[str, HealthStatus]


async def check_postgres() -> HealthStatus:
    """Check PostgreSQL database health."""
    try:
        await list_agents_query(
            developer_id=UUID("00000000-0000-0000-0000-000000000000"),
        )
        return "ok"
    except Exception as e:
        logging.error("Postgres health check failed: %s", str(e))
        return "error"


async def check_temporal() -> HealthStatus:
    """Check Temporal service health."""
    try:
        client = await get_client()
        await client.count_workflows()
        return "ok"
    except Exception as e:
        logging.error("Temporal health check failed: %s", str(e))
        return "error"


async def check_litellm() -> HealthStatus:
    """Check LiteLLM service health."""
    try:
        await litellm.get_model_list()
        return "ok"
    except Exception as e:
        logging.error("LiteLLM health check failed: %s", str(e))
        return "error"


async def check_integration_service() -> HealthStatus:
    """Check Integration service health."""
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
