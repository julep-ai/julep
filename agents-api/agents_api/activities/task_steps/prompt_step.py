import asyncio

from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import ChatSettings, InputChatMLMessage
from ...clients import (
    litellm,  # We dont directly import `acompletion` so we can mock it
)
from ...common.protocol.tasks import StepContext, StepOutcome
from ...common.utils.template import render_template


@activity.defn
@beartype
async def prompt_step(context: StepContext) -> StepOutcome:
    # Get context data
    context_data: dict = context.model_dump()

    # Render template messages
    prompt = (
        [InputChatMLMessage(content=context.current_step.prompt)]
        if isinstance(context.current_step.prompt, str)
        else context.current_step.prompt
    )

    template_messages: list[InputChatMLMessage] = prompt
    messages = await asyncio.gather(
        *[
            render_template(msg.content, context_data, skip_vars=["developer_id"])
            for msg in template_messages
        ]
    )

    messages = [
        (
            InputChatMLMessage(role="user", content=m)
            if isinstance(m, str)
            else InputChatMLMessage(**m)
        )
        for m in messages
    ]

    # Get settings and run llm
    settings: ChatSettings = context.current_step.settings or ChatSettings()
    settings_data: dict = settings.model_dump()

    response = await litellm.acompletion(
        messages=messages,
        **settings_data,
    )

    return StepOutcome(
        output=response.model_dump(),
        next=None,
    )
