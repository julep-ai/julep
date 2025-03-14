from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query

from ...autogen.openapi_model import Includable, Response
from ...dependencies.developer_id import get_developer_id
from .router import router


@router.get("/responses/{response_id}", tags=["responses"])
async def get_response(
    response_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    include: Annotated[list[Includable], Query()] = [],
) -> Response:
    # TODO: Implement the logic to get a response by id
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
                    "annotations": []
                    }
                ]
                }
            ],
            "parallel_tool_calls": True,
            "previous_response_id": None,
            "reasoning": {
                "effort": None,
                "summary": None
            },
            "store": True,
            "temperature": 1.0,
            "text": {
                "format": {
                "type": "text"
                }
            },
            "tool_choice": "auto",
            "tools": [],
            "top_p": 1.0,
            "truncation": "disabled",
            "usage": {
                "input_tokens": 32,
                "input_tokens_details": {
                "cached_tokens": 0
                },
                "output_tokens": 18,
                "output_tokens_details": {
                "reasoning_tokens": 0
                },
                "total_tokens": 50
            },
            "user": None,
            "metadata": {}
            }
