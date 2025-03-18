from uuid import UUID

from ...autogen.Chat import (
    ChatInput,
    Content,
    ContentModel7,
    CreateToolRequest,
    ImageUrl,
    Message,
)
from ...autogen.openapi_model import (
    Agent,
    ChatResponse,
    CompletionUsage,
    CreateAgentRequest,
    CreateEntryRequest,
    CreateResponse,
    CreateSessionRequest,
    InputTokensDetails,
    OutputTokensDetails,
    Response,
    ResponseUsage,
    Session,
)
from ...autogen.Responses import (
    ComputerToolCall,
    FileSearchToolCall,
    FunctionToolCall,
    InputImage,
    InputText,
    OutputMessage,
    OutputText,
    ReasoningItem,
    WebSearchToolCall,
)
from ...autogen.Tools import FunctionDef
from ...queries.agents.create_agent import create_agent as create_agent_query
from ...queries.agents.list_agents import list_agents as list_agents_query
from ...queries.entries import add_entry_relations, create_entries, get_history
from ...queries.sessions.create_session import create_session as create_session_query
from ...queries.sessions.get_session import get_session as get_session_query


async def convert_create_response(
    developer_id: UUID, create_response: CreateResponse
) -> tuple[Agent, Session, ChatInput]:
    agents = await list_agents_query(
        developer_id=developer_id,
    )

    # Sessions cannot be created without an agent. So:
    # - If there is an agent, use it
    # - If there is no agent, create a draft agent and use it
    if agents:
        agent = agents[0]
    else:
        agent = await create_agent_query(
            developer_id=developer_id,
            data=CreateAgentRequest(
                name="draft-agent-for-response",
                about="Draft agent for response",
                model=create_response.model,
            ),
        )

    # Session ids are treated as previous_response_ids. So:
    # - If there is a previous_response_id, use it
    # - If there is no previous_response_id, create a session and use its id as the previous_response_id
    session_id = create_response.previous_response_id
    previous_session = None
    if session_id:
        # TODO: Handle case where previous_response_id is provided, but session is not found
        previous_session: Session = await get_session_query(
            developer_id=developer_id,
            session_id=UUID(session_id),
        )

    session = await create_session_query(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            system_template=create_response.instructions or "You are a helpful assistant.",
            metadata=create_response.metadata,
        ),
    )

    if previous_session:
        history = await get_history(
            developer_id=developer_id,
            session_id=previous_session.id,
        )
        entry_requests = []
        for entry in history.entries:
            entry_data = entry.model_dump(mode="json")
            if "id" in entry_data:
                del entry_data["id"]
            if "created_at" in entry_data:
                del entry_data["created_at"]

            entry_request = CreateEntryRequest(**entry_data)
            entry_requests.append(entry_request)

        await create_entries(
            developer_id=developer_id,
            session_id=session.id,
            data=entry_requests,
        )
        await add_entry_relations(
            developer_id=developer_id,
            session_id=session.id,
            data=history.relations,
        )
    # Unsupported fields from `CreateResponse` that are not supported by `ChatInput` or `Session`:
    # - include
    # - parallel_tool_calls
    # - response_format
    # - n
    # - user
    # - reasoning
    # - text
    # - truncation

    messages: list[Message] = []

    if isinstance(create_response.input, str):
        messages = [Message(role="user", content=[Content(text=create_response.input)])]
    else:
        # Create a ChatInput object from each InputItem object in the input list
        for item in create_response.input:
            for content_item in item.content:
                content = None
                if content_item.type == "input_text" and isinstance(content_item, InputText):
                    content = [Content(text=content_item.text)]
                elif content_item.type == "input_image" and isinstance(
                    content_item, InputImage
                ):
                    image_url = ImageUrl(
                        url=content_item.image_url,
                    )
                    content = [ContentModel7(image_url=image_url)]

                if content:
                    messages.append(Message(role=item.role, content=content))
                else:
                    msg = f"Unsupported content type: {content_item.type}. Content item: {content_item}"
                    raise ValueError(msg)

    # TODO: Convert tools from `CreateResponse` to `ChatInput`
    tools: list[CreateToolRequest] = []

    if create_response.tools:
        for tool in create_response.tools:
            if tool.type == "function":
                # tools.append(
                #     {
                #         "type": "function",
                #         "name": tool.name,
                #         "description": tool.description,
                #         "parameters": tool.parameters,
                #     }
                # )

                tools.append(
                    CreateToolRequest(
                        name=tool.name,
                        description=tool.description,
                        type="function",
                        function=FunctionDef(
                            name=tool.name,
                            description=tool.description,
                            parameters=tool.parameters,
                        ),
                    )
                )
            elif (
                tool.type == "web_search_preview"
                or tool.type == "file_search"
                or tool.type == "computer-preview"
            ):
                tools.append(
                    CreateToolRequest(
                        name=tool.name,
                        type=tool.type,
                    )
                )

    chat_input = ChatInput(
        model=create_response.model,
        messages=messages,
        save=create_response.store,
        stream=create_response.stream,
        max_tokens=create_response.max_tokens,
        temperature=create_response.temperature,
        presence_penalty=create_response.presence_penalty,
        frequency_penalty=create_response.frequency_penalty,
        top_p=create_response.top_p,
        stop=create_response.stop or [],
        logit_bias=create_response.logit_bias,
        tool_choice=create_response.tool_choice,
        tools=tools,
        truncation=create_response.truncation,
        recall=False,  # TODO: Enable recall only when file_search tool is present
    )

    return agent, session, chat_input


def convert_chat_response_to_response(
    create_response: CreateResponse,
    chat_response: ChatResponse,
    chat_input: ChatInput,
    session_id: UUID,
    user_id: UUID,
) -> Response:
    chat_response_usage: CompletionUsage | None = chat_response.usage

    if chat_response_usage is None:
        usage = ResponseUsage(
            input_tokens=0,
            input_tokens_details=InputTokensDetails(cached_tokens=0),
            output_tokens=0,
            output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
            total_tokens=0,
        )
    else:
        usage = ResponseUsage(
            input_tokens=chat_response_usage.prompt_tokens or 0,
            # FIXME: Placeholder. Need to add proper input_tokens_details
            input_tokens_details=InputTokensDetails(cached_tokens=0),
            output_tokens=chat_response_usage.completion_tokens or 0,
            # FIXME: Placeholder. Need to add proper output_tokens_details
            output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
            total_tokens=chat_response_usage.total_tokens or 0,
        )

    output: list[
        OutputMessage
        | FileSearchToolCall
        | FunctionToolCall
        | WebSearchToolCall
        | ComputerToolCall
        | ReasoningItem
    ] = []

    for choice in chat_response.choices:
        if choice.finish_reason == "tool_calls":
            pass
            # output.append(
            #     FunctionToolCall(

            #     )
        else:
            output_text = chat_response.choices[0].message.content
            output.append(
                OutputMessage(
                    type="message",
                    id=str(chat_response.id),
                    status="completed",
                    role="assistant",
                    content=[OutputText(text=output_text, annotations=[])],
                )
            )

    return Response(
        id=str(session_id),
        created_at=int(chat_response.created_at.timestamp()),
        status="completed",  # because we don't have get endpoint
        error=None,
        incomplete_details=None,
        instructions=create_response.instructions,
        max_output_tokens=create_response.max_tokens,  # TODO: is it the same as chat_input.max_tokens?
        model=chat_input.model,
        output=output,
        parallel_tool_calls=create_response.parallel_tool_calls,
        previous_response_id=create_response.previous_response_id,
        reasoning=create_response.reasoning,  # TODO: add reasoning (or not?)
        store=chat_input.save,
        temperature=chat_input.temperature,
        text=create_response.text or {"format": {"type": "text"}},
        tool_choice="auto",  # Default to auto if None
        tools=[],  # Default to empty list if None
        top_p=chat_input.top_p,
        truncation="auto",  # Default to auto if None
        usage=usage,
        user=str(user_id),
        metadata=create_response.metadata or {},
    )
