from functools import partial
from typing import Annotated
from uuid import UUID

import anyio
import httpx
from anyio.streams.memory import MemoryObjectSendStream
from fastapi import Depends, Request
from sse_starlette.sse import EventSourceResponse

from ...dependencies.developer_id import get_developer_id
from ...env import hasura_admin_secret, hasura_url
from .router import router

# Poll interval in seconds between status checks
STREAM_POLL_INTERVAL = 1
# Overall timeout for the SSE connection (seconds)
STREAM_TIMEOUT = 10 * 60


async def execution_status_publisher(
    send_chan: MemoryObjectSendStream,
    execution_id: UUID,
    x_developer_id: UUID,
    request: Request,
):
    async with send_chan:
        last_updated_at: str | None = None
        # Prepare headers for Hasura
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if hasura_admin_secret:
            headers["x-hasura-admin-secret"] = hasura_admin_secret
        # Optionally include developer ID header if required by Hasura permissions
        headers["x-hasura-user-id"] = str(x_developer_id)

        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                # exit loop if client disconnected
                if await request.is_disconnected():
                    break
                # GraphQL query to fetch latest execution status
                query = """
                query ExecutionStatus($execution_id: uuid!) {
                  latest_executions(
                    where: { execution_id: { _eq: $execution_id } }
                  ) {
                    execution_id
                    status
                    updated_at
                    error
                  }
                }
                """
                payload = {"query": query, "variables": {"execution_id": str(execution_id)}}
                try:
                    resp = await client.post(
                        hasura_url + "/v1/graphql", json=payload, headers=headers
                    )
                    resp.raise_for_status()
                    result = resp.json().get("data", {}).get("latest_executions", [])
                except httpx.HTTPError:
                    # transient error: wait and retry
                    await anyio.sleep(STREAM_POLL_INTERVAL)
                    continue
                if result:
                    row = result[0]
                    updated_at = row.get("updated_at")
                    if updated_at and updated_at != last_updated_at:
                        last_updated_at = updated_at
                        try:
                            await send_chan.send({"data": row})
                        except anyio.BrokenResourceError:
                            break
                # wait before polling again
                await anyio.sleep(STREAM_POLL_INTERVAL)


@router.get(
    "/executions/{execution_id}/status.stream",
    response_class=EventSourceResponse,
    tags=["executions"],
)
async def stream_execution_status(
    request: Request,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    execution_id: UUID,
):
    """
    SSE endpoint that streams the status of a given execution_id by polling the
    latest_executions view in Hasura.
    """

    send_chan, recv_chan = anyio.create_memory_object_stream(max_buffer_size=1)
    return EventSourceResponse(
        recv_chan,
        data_sender_callable=partial(
            execution_status_publisher, send_chan, execution_id, x_developer_id, request
        ),
        send_timeout=STREAM_TIMEOUT,
    )
