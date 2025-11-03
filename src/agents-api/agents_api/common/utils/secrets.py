from datetime import timedelta
from uuid import UUID

from temporalio import workflow
from temporalio.workflow import _NotInWorkflowEventLoopError

from ...activities.pg_query_step import pg_query_step
from ...autogen.openapi_model import Secret
from ...env import temporal_heartbeat_timeout
from ...queries.secrets import get_secret_by_name as get_secret_by_name_query
from ...queries.secrets.list import list_secrets_query
from ..exceptions.secrets import (
    SecretNotFoundError,  # AIDEV-NOTE: use domain exception for missing secrets
)
from ..retry_policies import DEFAULT_RETRY_POLICY


async def get_secret_by_name(developer_id: UUID, name: str, decrypt: bool = False) -> Secret:
    """Fetch a developer secret by name without caching to avoid cross-loop futures."""
    try:
        secret = await workflow.execute_activity(
            pg_query_step,
            args=[
                "get_secret_by_name",
                "secrets.get_by_name",
                {"developer_id": developer_id, "name": name, "decrypt": decrypt},
            ],
            schedule_to_close_timeout=timedelta(days=31),
            retry_policy=DEFAULT_RETRY_POLICY,
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )
    except _NotInWorkflowEventLoopError:
        secret = await get_secret_by_name_query(
            developer_id=developer_id,
            name=name,
            decrypt=decrypt,
        )

    if secret is None:
        raise SecretNotFoundError(developer_id, name)

    return secret


async def get_secrets_list(
    developer_id: UUID,
    decrypt: bool = False,
    connection_pool=None,
) -> list[Secret]:
    """Return the full secret list without shared caching (avoids loop mismatches)."""
    try:
        secrets_query_result = await workflow.execute_activity(
            pg_query_step,
            args=[
                "list_secrets_query",
                "secrets.list",
                {"developer_id": developer_id, "decrypt": decrypt},
            ],
            schedule_to_close_timeout=timedelta(days=31),
            retry_policy=DEFAULT_RETRY_POLICY,
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )
    except _NotInWorkflowEventLoopError:
        secrets_query_result = await list_secrets_query(
            developer_id=developer_id,
            decrypt=decrypt,
            connection_pool=connection_pool,
        )

    return secrets_query_result
