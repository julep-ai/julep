from datetime import timedelta
from uuid import UUID

from async_lru import alru_cache
from temporalio import workflow
from temporalio.workflow import _NotInWorkflowEventLoopError

from ...activities.pg_query_step import pg_query_step
from ...autogen.openapi_model import Secret
from ...env import secrets_cache_ttl, temporal_heartbeat_timeout
from ...queries.secrets import get_secret_by_name as get_secret_by_name_query
from ...queries.secrets.list import list_secrets_query
from ..exceptions.secrets import (
    SecretNotFoundError,  # AIDEV-NOTE: use domain exception for missing secrets
)
from ..retry_policies import DEFAULT_RETRY_POLICY


@alru_cache(ttl=secrets_cache_ttl)
async def get_secret_by_name(developer_id: UUID, name: str, decrypt: bool = False) -> Secret:
    # FIXME: Should use workflow.in_workflow() instead ?
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

    # AIDEV-NOTE: use domain-specific exception instead of HTTPException
    if secret is None:
        raise SecretNotFoundError(developer_id, name)

    return secret

@alru_cache(ttl=secrets_cache_ttl)
async def get_secrets_list(
    developer_id: UUID, 
    decrypt: bool = False, 
    connection_pool=None
) -> list[Secret]:
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
