import logging
from base64 import b64decode, b64encode
from functools import partial
from typing import Annotated
from uuid import UUID

import anyio
from anyio.streams.memory import MemoryObjectSendStream
from fastapi import Depends, Query
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request
from temporalio.api.enums.v1 import EventType
from temporalio.client import (
    WorkflowHistoryEventAsyncIterator,
    WorkflowHistoryEventFilterType,
)

from ...autogen.openapi_model import TransitionEvent
from ...clients.temporal import get_workflow_handle
from ...dependencies.developer_id import get_developer_id
from ...models.execution.lookup_temporal_data import lookup_temporal_data
from ...worker.codec import from_payload_data
from .router import router

STREAM_TIMEOUT = 10 * 60  # 10 minutes


# Create a function to publish events to the client
# TODO: Unnest and simplify this function
async def event_publisher(
    inner_send_chan: MemoryObjectSendStream,
    history_events: WorkflowHistoryEventAsyncIterator,
):
    async with inner_send_chan:
        try:
            async for event in history_events:
                # TODO: We should get the workflow-completed event as well and use that to close the stream
                if event.event_type == EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED:
                    payloads = (
                        event.activity_task_completed_event_attributes.result.payloads
                    )

                    for payload in payloads:
                        try:
                            data_item = from_payload_data(payload.data)

                        except Exception as e:
                            logging.warning(f"Could not decode payload: {e}")
                            continue

                        if not isinstance(data_item, TransitionEvent):
                            continue

                        # FIXME: This does NOT return the last event (and maybe other events)
                        transition_event_dict = dict(
                            type=data_item.type,
                            output=data_item.output,
                            created_at=data_item.created_at.isoformat(),
                        )

                        next_page_token = (
                            b64encode(history_events.next_page_token).decode("ascii")
                            if history_events.next_page_token
                            else None
                        )

                        await inner_send_chan.send(
                            dict(
                                data=dict(
                                    transition=transition_event_dict,
                                    next_page_token=next_page_token,
                                ),
                            )
                        )

        except anyio.get_cancelled_exc_class() as e:
            with anyio.move_on_after(STREAM_TIMEOUT, shield=True):
                await inner_send_chan.send(dict(closing=True))
                raise e


@router.get("/executions/{execution_id}/transitions.stream", tags=["executions"])
async def stream_transitions_events(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    execution_id: UUID,
    req: Request,
    next_page_token: Annotated[str | None, Query()] = None,
):
    # Get temporal id
    temporal_data = lookup_temporal_data(
        developer_id=x_developer_id,
        execution_id=execution_id,
    )

    # TODO: Need to get all the events for child workflows too. Maybe try the `run_id` or something?
    # SCRUM-11
    workflow_handle = await get_workflow_handle(
        handle_id=temporal_data["id"],
    )

    next_page_token: bytes | None = (
        b64decode(next_page_token) if next_page_token else None
    )

    history_events = workflow_handle.fetch_history_events(
        page_size=1,
        next_page_token=next_page_token,
        wait_new_event=True,
        event_filter_type=WorkflowHistoryEventFilterType.ALL_EVENT,
        skip_archival=True,
    )

    # Create a channel to send events to the client
    send_chan, recv_chan = anyio.create_memory_object_stream(max_buffer_size=100)

    return EventSourceResponse(
        recv_chan,
        data_sender_callable=partial(event_publisher, send_chan, history_events),
    )
