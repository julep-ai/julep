from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Query

from ...autogen.Entries import History
from ...autogen.openapi_model import (
    Includable,
    InputTokensDetails,
    OutputMessage,
    OutputText,
    OutputTokensDetails,
    ResponseUsage,
    Text,
)
from ...autogen.Responses import (
    ComputerToolCall,
    FileSearchToolCall,
    FunctionToolCall,
    ReasoningItem,
    Response,
    ResponseFormatText,
    WebSearchToolCall,
)
from ...common.protocol.developers import Developer
from ...dependencies.developer_id import get_developer_data
from ...queries.entries.get_history import get_history as get_history_query
from .router import router


@router.get("/responses/{response_id}", tags=["responses"])
async def get_response(
    response_id: UUID,
    developer: Annotated[Developer, Depends(get_developer_data)],
    include: Annotated[list[Includable], Query()] = [],
) -> Response:
    # TODO: Continue the implementation of the logic to get a response by id

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

    if not last_entries:
        raise HTTPException(
            status_code=404, detail="No response was found for the provided response id"
        )

    last_entry = last_entries[-1]

    output: list[
        OutputMessage
        | FileSearchToolCall
        | FunctionToolCall
        | WebSearchToolCall
        | ComputerToolCall
        | ReasoningItem
    ] = []

    for entry in last_entries:
        if entry.tool_calls:
            for tool_call in entry.tool_calls:
                if tool_call.type == "function":
                    # Specific case of the mapped `web_search_preview` tool call
                    if tool_call.function.name == "web_search_preview":
                        output.append(
                            WebSearchToolCall(
                                id=tool_call.id,
                                status="completed",
                            )
                        )
                    else:
                        # Generic case for all other `function` tool calls
                        output.append(
                            FunctionToolCall(
                                id=tool_call.id,
                                call_id=tool_call.id,  # FIXME: Check this
                                name=tool_call.function.name,
                                arguments=tool_call.function.arguments,
                                status="completed",
                            )
                        )
        else:
            output.append(
                OutputMessage(
                    type="message",
                    id=str(entry.id),
                    status="completed",
                    role=entry.role,
                    content=[
                        OutputText(
                            type="output_text",
                            text=entry.content[0].text,
                            annotations=[],
                        )
                    ],
                )
            )

    return Response(
        id=str(response_id),
        object="response",
        created_at=int(last_entry.created_at.timestamp()),
        status="completed",
        error=None,
        incomplete_details=None,
        instructions=None,
        max_output_tokens=None,
        model=last_entry.model,
        output=output,
        parallel_tool_calls=True,
        previous_response_id=None,
        # FIXME: We are not storing reasoning. So returning None for now.
        reasoning=None,
        store=True,
        temperature=1.0,
        text=Text(format=ResponseFormatText(type="text")),  # FIXME: Add the correct format
        tool_choice="auto",
        tools=[],
        top_p=1.0,
        truncation="disabled",
        usage=ResponseUsage(
            input_tokens=0,
            input_tokens_details=InputTokensDetails(cached_tokens=0),
            output_tokens=sum(entry.token_count for entry in last_entries),
            output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
            total_tokens=sum(entry.token_count for entry in last_entries),
        ),
        user=None,
        metadata={},
    )
