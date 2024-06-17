import asyncio

# import celpy
from openai.types.chat.chat_completion import ChatCompletion
from temporalio import activity
from uuid import uuid4

from ...autogen.openapi_model import (
    PromptWorkflowStep,
    # EvaluateWorkflowStep,
    # YieldWorkflowStep,
    # ToolCallWorkflowStep,
    # ErrorWorkflowStep,
    # IfElseWorkflowStep,
    InputChatMLMessage,
)

from ...common.protocol.tasks import (
    StepContext,
    TransitionInfo,
)

from ...common.utils.template import render_template

from ...models.execution.create_execution_transition import (
    create_execution_transition_query,
)
from ...routers.sessions.session import llm_generate
from ...routers.sessions.protocol import Settings


@activity.defn
async def prompt_step(context: StepContext) -> dict:
    assert isinstance(context.definition, PromptWorkflowStep)

    # Get context data
    context_data: dict = context.model_dump()

    # Render template messages
    template_messages: list[InputChatMLMessage] = context.definition.prompt
    messages: list[InputChatMLMessage] = asyncio.gather(
        *[
            render_template(msg.content, context_data, skip_vars=["developer_id"])
            for msg in template_messages
        ]
    )

    # Get settings and run llm
    response: ChatCompletion = await llm_generate(
        messages,
        Settings(
            model=context.definition.settings.model or "gpt-4-turbo",
            response_format=None,
        ),
    )

    return response


# @activity.defn
# async def evaluate_step(context: StepContext) -> dict:
#     if not isinstance(context.definition, EvaluateWorkflowStep):
#         return {}

#     # FIXME: set the field to keep source code
#     source: str = context.definition.evaluate
#     env = celpy.Environment()
#     ast = env.compile(source)
#     prog = env.program(ast)
#     # TODO: set args
#     args = {}
#     result = prog.evaluate(args)
#     return {"result": result}


# @activity.defn
# async def yield_step(context: StepContext) -> dict:
#     if not isinstance(context.definition, YieldWorkflowStep):
#         return {}

#     # TODO: implement

#     return {"test": "result"}


# @activity.defn
# async def tool_call_step(context: StepContext) -> dict:
#     if not isinstance(context.definition, ToolCallWorkflowStep):
#         return {}

#     # TODO: implement

#     return {"test": "result"}


# @activity.defn
# async def error_step(context: StepContext) -> dict:
#     if not isinstance(context.definition, ErrorWorkflowStep):
#         return {}

#     return {"error": context.definition.error}


# @activity.defn
# async def if_else_step(context: StepContext) -> dict:
#     if not isinstance(context.definition, IfElseWorkflowStep):
#         return {}

#     return {"test": "result"}


@activity.defn
async def transition_step(
    developer_id: str,
    context: StepContext,
    transition_info: TransitionInfo,
) -> dict:
    print("Running transition step")
    assert NotImplementedError()

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

    # Raise if it's a waiting step
    if transition_info.type == "awaiting_input":
        activity.raise_complete_async()
