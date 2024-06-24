import asyncio

# import celpy
from openai.types.chat.chat_completion import ChatCompletion
from temporalio import activity
from uuid import uuid4

from ...autogen.openapi_model import (
    PromptWorkflowStep,
    InputChatMLMessage,
)

from ...common.protocol.tasks import (
    StepContext,
)

from ...common.utils.template import render_template

from ...routers.sessions.session import llm_generate
from ...routers.sessions.protocol import Settings
from ...clients.worker.types import ChatML


@activity.defn
async def prompt_step(context: StepContext) -> ChatCompletion:
    assert isinstance(context.definition, PromptWorkflowStep)

    # Get context data
    context_data: dict = context.model_dump()

    # Render template messages
    template_messages: list[InputChatMLMessage] = context.definition.prompt
    messages = await asyncio.gather(
        *[
            render_template(msg.content, context_data, skip_vars=["developer_id"])
            for msg in template_messages
        ]
    )

    messages = [
        ChatML(role="user", content=m) if isinstance(m, str) else ChatML(**m)
        for m in messages
    ]

    # Get settings and run llm
    response: ChatCompletion = await llm_generate(
        messages,
        Settings(
            model=context.definition.settings.model or "gpt-4-turbo",
            response_format=None,
        ),
    )

    return response


@activity.defn(name="prompt_step")
async def prompt_step_mocked(context: StepContext) -> ChatCompletion:
    return ChatCompletion(
        id=str(uuid4()),
        choices=[],
        created=0,
        model="gpt-4-turbo",
        object="chat.completion",
    )
