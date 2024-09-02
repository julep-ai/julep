from functools import partial
from typing import Annotated

import anyio
from anyio.streams.memory import MemoryObjectSendStream
from fastapi import Depends
from pydantic import UUID4
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

from ...dependencies.developer_id import get_developer_id
from .router import router


@router.get("/executions/{execution_id}/transitions.stream", tags=["executions"])
async def stream_transitions_events(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    execution_id: UUID4,
    req: Request,
    # FIXME: add support for page token
):
    # Create a channel to send events to the client
    send_chan, recv_chan = anyio.create_memory_object_stream(10)

    # Create a function to publish events to the client
    async def event_publisher(inner_send_chan: MemoryObjectSendStream):
        async with inner_send_chan:
            try:
                i = 0
                while True:
                    i += 1
                    await inner_send_chan.send(dict(data=i))
                    await anyio.sleep(1.0)
            except anyio.get_cancelled_exc_class() as e:
                with anyio.move_on_after(1, shield=True):
                    await inner_send_chan.send(dict(closing=True))
                    raise e

    return EventSourceResponse(
        recv_chan, data_sender_callable=partial(event_publisher, send_chan)
    )
