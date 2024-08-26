import asyncio

from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import (
    ChatSettings,
    Content,
    ContentModel,
    InputChatMLMessage,
)
from ...clients import (
    litellm,  # We dont directly import `acompletion` so we can mock it
)
from ...common.protocol.tasks import StepContext, StepOutcome
from ...common.utils.template import render_template


def _content_to_dict(
    content: str | list[str] | list[Content | ContentModel], role: str
) -> str | list[dict]:
    if isinstance(content, str):
        return content

    result = []
    for s in content:
        if isinstance(s, str):
            result.append({"content": {"type": "text", "text": s, "role": role}})
        elif isinstance(s, Content):
            result.append({"content": {"type": s.type, "text": s.text, "role": role}})
        elif isinstance(s, ContentModel):
            result.append(
                {
                    "content": {
                        "type": s.type,
                        "image_url": {"url": s.image_url.url},
                        "role": role,
                    }
                }
            )

    return result


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
            render_template(
                _content_to_dict(msg.content, msg.role),
                context_data,
                skip_vars=["developer_id"],
            )
            for msg in template_messages
        ]
    )

    result_messages = []
    for m in messages:
        if isinstance(m, str):
            msg = InputChatMLMessage(role="user", content=m)
        else:
            msg = []
            for d in m:
                role = d["content"].get("role")
                d["content"] = [d["content"]]
                d["role"] = role
                msg.append(InputChatMLMessage(**d))

        result_messages.append(msg)

    # messages = [
    #     (
    #         InputChatMLMessage(role="user", content=m)
    #         if isinstance(m, str)
    #         else [InputChatMLMessage(**d) for d in m]
    #     )
    #     for m in messages
    # ]

    # Get settings and run llm
    settings: ChatSettings = context.current_step.settings or ChatSettings()
    settings_data: dict = settings.model_dump()

    response = await litellm.acompletion(
        messages=result_messages,
        **settings_data,
    )

    return StepOutcome(
        output=response.model_dump(),
        next=None,
    )
