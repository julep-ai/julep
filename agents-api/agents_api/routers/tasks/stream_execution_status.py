import logging
from functools import partial
from typing import Annotated
from uuid import UUID

import anyio
from anyio.streams.memory import MemoryObjectSendStream
from fastapi import Depends, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse

from ...autogen.openapi_model import ExecutionStatusEvent
from ...dependencies.developer_id import get_developer_id
from ...queries.executions.get_execution_status import (
    get_execution_status as get_execution_status_query,
)
from .router import router

# Set up logger
logger = logging.getLogger(__name__)

# Poll interval in seconds between status checks
STREAM_POLL_INTERVAL = 1
# Overall timeout for the SSE connection (seconds)
STREAM_TIMEOUT = 10 * 60

# Terminal states that indicate we should end the stream
TERMINAL_STATES = {"succeeded", "failed", "cancelled"}


async def execution_status_publisher(
    send_chan: MemoryObjectSendStream,
    execution_id: UUID,
    x_developer_id: UUID,
    request: Request,
):
    """
    Publishes execution status updates to the SSE stream.
    
    Args:
        send_chan: Channel to send updates through
        execution_id: ID of the execution to monitor
        x_developer_id: Developer ID for permission checking
        request: FastAPI request object to check for disconnection
    """
    async with send_chan:
        last_updated_at: str | None = None
        while True:
            # Exit loop if client disconnected
            if await request.is_disconnected():
                logger.debug(f"Client disconnected from status stream for execution {execution_id}")
                break
                
            # Fetch latest execution status via SQL query
            try:
                execution_status_event: ExecutionStatusEvent = await get_execution_status_query(
                    developer_id=x_developer_id,
                    execution_id=execution_id,
                )
            except Exception as e:
                # Log the error and continue
                logger.error(f"Error fetching status for execution {execution_id}: {str(e)}")
                await anyio.sleep(STREAM_POLL_INTERVAL)
                continue

            if not execution_status_event:
                logger.warning(f"No status found for execution {execution_id}")
                await anyio.sleep(STREAM_POLL_INTERVAL)
                continue
                
            updated_at = execution_status_event.updated_at
            if updated_at and updated_at != last_updated_at:
                last_updated_at = updated_at
                try:
                    json_data = execution_status_event.model_dump_json()
                    await send_chan.send({"data": json_data})
                    
                    # Log terminal states
                    if execution_status_event.status in TERMINAL_STATES:
                        logger.info(
                            f"Execution {execution_id} reached terminal state: {execution_status_event.status}"
                        )
                        break
                        
                except anyio.BrokenResourceError as e:
                    logger.warning(f"Connection broken while sending status for execution {execution_id}: {str(e)}")
                    break
                except Exception as e:
                    logger.error(f"Error sending status for execution {execution_id}: {str(e)}")
                    # Continue the loop to try again
            
            # Wait before polling again
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
    try:
        try:
            # Verify execution exists before starting the stream
            await get_execution_status_query(
                developer_id=x_developer_id,
                execution_id=execution_id,
            )
        except HTTPException as e:
            if "not found" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Execution {execution_id} not found",
                )
            raise e

        send_chan, recv_chan = anyio.create_memory_object_stream(max_buffer_size=1)
        logger.debug(f"Starting status stream for execution {execution_id}")
        
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

    except Exception as e:
        error_message = f"Failed to start status stream for execution {execution_id}: {str(e)}"
        logger.error(error_message)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start execution status stream",
        )
