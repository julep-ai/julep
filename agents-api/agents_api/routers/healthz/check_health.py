from uuid import UUID

from ...autogen.openapi_model import Agent, ListResponse
from ...models.agent.list_agents import list_agents as list_agents_query
from .router import router


@router.get("/healthz", tags=["healthz"])
async def check_health() -> dict:
    try:
        # Check if the database is reachable
        agents = list_agents_query(
            developer_id=UUID("00000000-0000-0000-0000-000000000000"),
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "ok"}