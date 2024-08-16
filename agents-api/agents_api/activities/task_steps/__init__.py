import asyncio

from simpleeval import simple_eval
from temporalio import activity

from ...autogen.openapi_model import (
    CreateTransitionRequest,
    EvaluateStep,
    IfElseWorkflowStep,
    InputChatMLMessage,
    PromptStep,
    ToolCallStep,
    YieldStep,
)
from ...clients import (
    litellm,  # We dont directly import `acompletion` so we can mock it
)
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...common.utils.template import render_template
from ...models.execution.create_execution_transition import (
    create_execution_transition as create_execution_transition_query,
)


@activity.defn
async def prompt_step(context: StepContext[PromptStep]) -> StepOutcome:
    # Get context data
    context_data: dict = context.model_dump()

    # Render template messages
    prompt = (
        [InputChatMLMessage(content=context.definition.prompt)]
        if isinstance(context.definition.prompt, str)
        else context.definition.prompt
    )

    template_messages: list[InputChatMLMessage] = prompt
    messages = await asyncio.gather(
        *[
            render_template(msg.content, context_data, skip_vars=["developer_id"])
            for msg in template_messages
        ]
    )

    messages = [
        InputChatMLMessage(role="user", content=m)
        if isinstance(m, str)
        else InputChatMLMessage(**m)
        for m in messages
    ]

    settings: dict = context.definition.settings.model_dump()
    # Get settings and run llm
    response = await litellm.acompletion(
        messages=messages,
        **settings,
    )

    return StepOutcome(
        output=response.model_dump(),
        next=None,
    )


@activity.defn
async def evaluate_step(context: StepContext) -> dict:
    assert isinstance(context.definition, EvaluateStep)

    names = {}
    for i in context.inputs:
        names.update(i)

    return {
        "result": {
            k: simple_eval(v, names=names)
            for k, v in context.definition.evaluate.items()
        }
    }


@activity.defn
async def yield_step(context: StepContext) -> dict:
    if not isinstance(context.definition, YieldStep):
        return {}

    # TODO: implement

    return {"test": "result"}


@activity.defn
async def tool_call_step(context: StepContext) -> dict:
    assert isinstance(context.definition, ToolCallStep)

    context.definition.tool_id
    context.definition.arguments
    # get tool by id
    # call tool

    return {}


@activity.defn
async def if_else_step(context: StepContext[IfElseWorkflowStep]) -> dict:
    context_data: dict = context.model_dump()

    next_workflow = (
        context.definition.then
        if simple_eval(context.definition.if_, names=context_data)
        else context.definition.else_
    )

    return {"goto_workflow": next_workflow}


@activity.defn
async def transition_step(
    context: StepContext[None],
    transition_info: CreateTransitionRequest,
):
    need_to_wait = transition_info.type == "wait"

    # Get task token if it's a waiting step
    if need_to_wait:
        task_token = activity.info().task_token
        transition_info.task_token = task_token

    # Create transition
    activity.heartbeat("Creating transition in db")
    create_execution_transition_query(
        developer_id=context.developer_id,
        execution_id=context.execution.id,
        task_id=context.task.id,
        data=transition_info,
        update_execution_status=True,
    )

    # Raise if it's a waiting step
    if need_to_wait:
        activity.heartbeat("Starting to wait")
        activity.raise_complete_async()
