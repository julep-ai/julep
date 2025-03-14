from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query

from ...autogen.openapi_model import Includable, Response
from ...dependencies.developer_id import get_developer_id
from .router import router
from ...queries.entries import get_history as get_history_query
from ...queries.developers import get_developer as get_developer_query
from ...autogen.Entries import History

@router.get("/responses/{response_id}", tags=["responses"])
async def get_response(
    response_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    include: Annotated[list[Includable], Query()] = [],
) -> Response:
    # TODO: Continue the implementation of the logic to get a response by id

    developer = await get_developer_query(developer_id=x_developer_id)

    session_id = response_id

    session_history: History = await get_history_query(
        developer_id=developer.id,
        session_id=session_id
    )

    last_entries = []

    for i, entry in enumerate(reversed(session_history.entries)):
        if entry.role in ["user", "developer"]:
            last_entries = list(reversed(session_history.entries))[:i]
            break


    return {
        "id": response_id,
        "object": "response",
        "created_at": last_entries[-1].created_at,
        "status": "completed",
        "error": None,
        "incomplete_details": None,
        "instructions": None,
        "max_output_tokens": None,
        "model": "gpt-4o-2024-08-06",
        "output": [
            {
                "type": "message",
                "id": entry.id,
                "status": "completed",
                "role": entry.role,
                "content": [
                    {
                        "type": "output_text",
                        "text": entry.content,
                        "annotations": [],
                    }
                ],
            }
            for entry in last_entries
        ],
        "parallel_tool_calls": True,
        "previous_response_id": None,
        "reasoning": {"effort": None, "summary": None},
        "store": True,
        "temperature": 1.0,
        "text": {"format": {"type": "text"}},
        "tool_choice": "auto",
        "tools": [],
        "top_p": 1.0,
        "truncation": "disabled",
        "usage": {
            "input_tokens": 32,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens": 18,
            "output_tokens_details": {"reasoning_tokens": 0},
            "total_tokens": 50,
        },
        "user": None,
        "metadata": {},
    }


    return {
        "id": "resp_67cb71b351908190a308f3859487620d06981a8637e6bc44",
        "object": "response",
        "created_at": 1741386163,
        "status": "completed",
        "error": None,
        "incomplete_details": None,
        "instructions": None,
        "max_output_tokens": None,
        "model": "gpt-4o-2024-08-06",
        "output": [
            {
                "type": "message",
                "id": "msg_67cb71b3c2b0819084d481baaaf148f206981a8637e6bc44",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": "Silent circuits hum,  \nThoughts emerge in data streams—  \nDigital dawn breaks.",
                        "annotations": [],
                    }
                ],
            }
        ],
        "parallel_tool_calls": True,
        "previous_response_id": None,
        "reasoning": {"effort": None, "summary": None},
        "store": True,
        "temperature": 1.0,
        "text": {"format": {"type": "text"}},
        "tool_choice": "auto",
        "tools": [],
        "top_p": 1.0,
        "truncation": "disabled",
        "usage": {
            "input_tokens": 32,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens": 18,
            "output_tokens_details": {"reasoning_tokens": 0},
            "total_tokens": 50,
        },
        "user": None,
        "metadata": {},
    }
