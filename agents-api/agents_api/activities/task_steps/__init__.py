from temporalio import activity

from ...common.protocol.tasks import (
    StepContext,
)


@activity.defn
async def prompt_step(context: StepContext) -> dict:
    print("Running prompt step")
    return {"test": "result"}


@activity.defn
async def evaluate_step(context: StepContext) -> dict:
    print("Running prompt step")
    return {"test": "result"}


@activity.defn
async def yield_step(context: StepContext) -> dict:
    print("Running yield step")
    return {"test": "result"}


@activity.defn
async def tool_call_step(context: StepContext) -> dict:
    print("Running tool_call step")
    return {"test": "result"}


@activity.defn
async def error_step(context: StepContext) -> dict:
    print("Running error step")
    return {"test": "result"}


@activity.defn
async def if_else_step(context: StepContext) -> dict:
    print("Running if_else step")
    return {"test": "result"}


@activity.defn
async def transition_step(
    context: StepContext, start: tuple[str, int], result: dict
) -> dict:
    print("Running transition step")
    return {"test": "result"}
