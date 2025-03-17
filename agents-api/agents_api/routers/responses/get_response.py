from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Query

from ...autogen.Entries import History
from ...autogen.openapi_model import Includable, Response
from ...dependencies.developer_id import get_developer_id
from ...queries.developers import get_developer as get_developer_query
from ...queries.entries import get_history as get_history_query
from .router import router


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
        developer_id=developer.id, session_id=session_id
    )

    if not session_history.entries:
        raise HTTPException(status_code=404, detail="Provided response id does not exist")

    last_entries = []

    for i, entry in enumerate(reversed(session_history.entries)):
        if entry.role in ["user", "developer"]:
            # Take all entries after the current entry
            last_entries = session_history.entries[len(session_history.entries) - i :]
            break

    last_entry = last_entries[-1]

    return {
        "id": str(response_id),
        "object": "response",
        "created_at": int(last_entry.created_at.timestamp()),
        "status": "completed",
        "error": None,
        "incomplete_details": None,
        "instructions": None,
        "max_output_tokens": None,
        "model": last_entry.model,
        "output": [
            {
                "type": "message",
                "id": str(entry.id),
                "status": "completed",
                "role": entry.role,
                "content": [
                    {
                        "type": "output_text",
                        "text": entry.content[0].text,
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
            "input_tokens": 0,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens": sum(entry.token_count for entry in last_entries),
            "output_tokens_details": {"reasoning_tokens": 0},
            "total_tokens": sum(entry.token_count for entry in last_entries),
        },
        "user": None,
        "metadata": {},
    }
