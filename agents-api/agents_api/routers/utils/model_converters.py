from uuid import UUID

from ...autogen.openapi_model import (
    Agent,
    ChatInput,
    ChatResponse,
    CreateAgentRequest,
    CreateEntryRequest,
    CreateResponse,
    CreateSessionRequest,
    MessageOutputItem,
    Response,
    ResponseUsage,
    Session,
    TextContentPart,
)
from ...queries.agents import create_agent as create_agent_query
from ...queries.agents import list_agents as list_agents_query
from ...queries.entries import add_entry_relations, create_entries, get_history
from ...queries.sessions import create_session as create_session_query
from ...queries.sessions import get_session as get_session_query


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

    chat_input = ChatInput(
        model=create_response.model,
        messages=[{"role": "user", "content": create_response.input}]
        if isinstance(create_response.input, str)
        else create_response.input,
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
        tools=create_response.tools,
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
    usage = ResponseUsage(
        input_tokens=chat_response.usage.prompt_tokens,
        input_tokens_details={
            "cached_tokens": 0
        },  # FIXME: Placeholder. Need to add proper input_tokens_details
        output_tokens=chat_response.usage.completion_tokens,
        output_tokens_details={
            "reasoning_tokens": 0
        },  # FIXME: Placeholder. Need to add proper output_tokens_details
        total_tokens=chat_response.usage.total_tokens,
    )

    output_text = chat_response.choices[0].message.content

    output: list[MessageOutputItem] = [
        MessageOutputItem(
            type="message",
            id=str(chat_response.id),
            status="completed",
            role="assistant",
            content=[TextContentPart(type="output_text", text=output_text, annotations=[])],
        ),
    ]
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
