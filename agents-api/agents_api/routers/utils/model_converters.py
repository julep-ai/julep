from uuid import UUID

from ...autogen.openapi_model import (
    ChatInput,
    ChatResponse,
    CreateResponse,
    Response,
)


def convert_create_response_to_chat_input(create_response: CreateResponse) -> ChatInput:
    return ChatInput(
        model=create_response.model,
        input=create_response.input,
        include=create_response.include,
        parallel_tool_calls=create_response.parallel_tool_calls,
        save=create_response.store,
        stream=create_response.stream,
        max_tokens=create_response.max_tokens,
        temperature=create_response.temperature,
        top_p=create_response.top_p,
        n=create_response.n,
        stop=create_response.stop,
        presence_penalty=create_response.presence_penalty,
        frequency_penalty=create_response.frequency_penalty,
        logit_bias=create_response.logit_bias,
        user=create_response.user,
        instructions=create_response.instructions,
        previous_response_id=create_response.previous_response_id,
        reasoning=create_response.reasoning,
        text=create_response.text,
        tool_choice=create_response.tool_choice,
        tools=create_response.tools,
        truncation=create_response.truncation,
        metadata=create_response.metadata,
    )


def convert_chat_response_to_response(
    chat_response: ChatResponse,
    chat_input: ChatInput,
    session_id: UUID,
    user_id: UUID,
) -> Response:
    return Response(
        id=chat_response.id,
        object=chat_response.object,
        created_at=chat_response.created_at,
        status="completeed",  # because we don't have get endpoint
        error=None,
        incomplete_details=None,
        instructions=None,  # TODO: Add instructions
        max_output_tokens=None,  # TODO: Add max_output_tokens (is it the same as chat_input.max_tokens?)
        model=chat_input.model,
        output=chat_response.output,  # TODO: fetch from chat_response.choices
        output_text=chat_response.output_text,  # TODO: fetch from chat_response.choices
        parallel_tool_calls=None,  # TODO: add parallel_tool_calls
        previous_response_id=session_id,
        reasoning=None,  # TODO: add reasoning (or not?)
        store=chat_input.save,
        temperature=chat_input.temperature,
        text=None,  # TODO: add text
        tool_choice=chat_input.tool_choice,
        tools=chat_input.tools,
        top_p=chat_input.top_p,
        truncation=None,  # TODO: add truncation
        usage=None,  # TODO: add usage
        user=user_id,
        metadata=None,  # TODO: add metadata
    )
