from functools import partial
from typing import Annotated
from uuid import UUID

import anyio
from anyio.streams.memory import MemoryObjectSendStream
from fastapi import Depends, Request
from sse_starlette.sse import EventSourceResponse

from ...dependencies.developer_id import get_developer_id
from ...queries.executions.get_execution_status import (
    get_execution_status as get_execution_status_query,
)
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
        while True:
            # exit loop if client disconnected
            if await request.is_disconnected():
                break
            # Fetch latest execution status via SQL query
            try:
                row = await get_execution_status_query(
                    developer_id=x_developer_id,
                    execution_id=execution_id,
                )
            except Exception:
                # transient DB error: wait and retry
                await anyio.sleep(STREAM_POLL_INTERVAL)
                continue

            if row:
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
    latest_executions view.
    """

    send_chan, recv_chan = anyio.create_memory_object_stream(max_buffer_size=1)
    return EventSourceResponse(
        recv_chan,
        data_sender_callable=partial(
            execution_status_publisher,
            send_chan,
            execution_id,
            x_developer_id,
            request,
        ),
        send_timeout=STREAM_TIMEOUT,
    )
