
from beartype import beartype
from temporalio import activity
from temporalio.exceptions import ApplicationError

from ...autogen.openapi_model import (
    Content,
    ContentModel,
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
    prompt: str | list[dict] = context.current_step.model_dump()["prompt"]
    context_data: dict = context.model_dump()

    # Render template messages
    prompt = await render_template(
        prompt,
        context_data,
        skip_vars=["developer_id"],
    )

    # Get settings and run llm
    agent_default_settings: dict = (
        context.execution_input.agent.default_settings.model_dump()
        if context.execution_input.agent.default_settings
        else {}
    )
    agent_model: str = (
        context.execution_input.agent.model
        if context.execution_input.agent.model
        else "gpt-4o"
    )

    if context.current_step.settings:
        passed_settings: dict = context.current_step.settings.model_dump(
            exclude_unset=True
        )
    else:
        passed_settings: dict = {}

    completion_data: dict = {
        "model": agent_model,
        ("messages" if isinstance(prompt, list) else "prompt"): prompt,
        **agent_default_settings,
        **passed_settings,
    }

    response = await litellm.acompletion(
        **completion_data,
    )

    return StepOutcome(
        output=response.model_dump(),
        next=None,
    )
