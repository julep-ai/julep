from datetime import timedelta
from uuid import UUID

from temporalio import workflow
from temporalio.workflow import _NotInWorkflowEventLoopError

from ...activities.pg_query_step import pg_query_step
from ...autogen.openapi_model import Secret
from ...env import temporal_heartbeat_timeout
from ...queries.secrets import get_secret_by_name as get_secret_by_name_query
from ..retry_policies import DEFAULT_RETRY_POLICY


async def get_secret_by_name(developer_id: UUID, name: str) -> Secret:
    try:
        secret = await workflow.execute_activity(
            pg_query_step,
            args=[
                "get_secret_by_name",
                "secrets.get_by_name",
                {"developer_id": developer_id, "name": name},
            ],
            schedule_to_close_timeout=timedelta(days=31),
            retry_policy=DEFAULT_RETRY_POLICY,
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )
    except _NotInWorkflowEventLoopError:
        print("*" * 1000)
        print("EXCEPTION")
        print("*" * 1000)
        secret = await get_secret_by_name_query(developer_id=developer_id, name=name)
    return secret
