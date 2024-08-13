import asyncio
from typing import Literal
from uuid import uuid4

from simpleeval import simple_eval
from temporalio import activity

from ...autogen.openapi_model import (
    EvaluateStep,
    IfElseWorkflowStep,
    InputChatMLMessage,
    PromptStep,
    ToolCallStep,
    UpdateExecutionRequest,
    YieldStep,
)
from ...clients import (
    litellm,  # We dont directly import `acompletion` so we can mock it
)
from ...clients.worker.types import ChatML
from ...common.protocol.tasks import (
    StepContext,
    TransitionInfo,
)
from ...common.utils.template import render_template
from ...models.execution.create_execution_transition import (
    create_execution_transition as create_execution_transition_query,
)
from ...models.execution.update_execution import (
    update_execution as update_execution_query,
)


@activity.defn
async def prompt_step(context: StepContext) -> dict:
    assert isinstance(context.definition, PromptStep)

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
        ChatML(role="user", content=m) if isinstance(m, str) else ChatML(**m)
        for m in messages
    ]

    settings: dict = context.definition.settings.model_dump()
    # Get settings and run llm
    response = await litellm.acompletion(
        messages=messages,
        **settings,
    )

    return response.model_dump()


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
async def if_else_step(context: StepContext) -> dict:
    assert isinstance(context.definition, IfElseWorkflowStep)

    context_data: dict = context.model_dump()
    next_workflow = (
        context.definition.then
        if simple_eval(context.definition.if_, names=context_data)
        else context.definition.else_
    )

    return {"goto_workflow": next_workflow}


@activity.defn
async def transition_step(
    context: StepContext,
    transition_info: TransitionInfo,
    execution_status: Literal[
        "queued",
        "starting",
        "running",
        "awaiting_input",
        "succeeded",
        "failed",
        "cancelled",
    ] = "awaiting_input",
):
    print("Running transition step")
    # raise NotImplementedError()

    # Get transition info
    transition_data = transition_info.model_dump(by_alias=False)

    # Get task token if it's a waiting step
    if transition_info.type == "awaiting_input":
        task_token = activity.info().task_token
        transition_data["__task_token"] = task_token

    # Create transition
    create_execution_transition_query(
        developer_id=context.developer_id,
        execution_id=context.execution.id,
        transition_id=uuid4(),
        **transition_data,
    )

    update_execution_query(
        developer_id=context.developer_id,
        task_id=context.task.id,
        execution_id=context.execution.id,
        data=UpdateExecutionRequest(
            status=execution_status,
        ),
    )

    # Raise if it's a waiting step
    if execution_status == "awaiting_input":
        activity.raise_complete_async()
