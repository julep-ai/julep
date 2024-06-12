import celpy
from temporalio import activity
from jinja2 import Environment

from agents_api.autogen.openapi_model import (
    PromptWorkflowStep, 
    EvaluateWorkflowStep, 
    YieldWorkflowStep,
    ToolCallWorkflowStep,
    ErrorWorkflowStep,
    IfElseWorkflowStep,
)
from ...common.protocol.tasks import (
    StepContext,
)


@activity.defn
async def prompt_step(context: StepContext) -> dict:
    # TODO: get the template string somehow
    template_str = "..."
    if not isinstance(context.definition, PromptWorkflowStep):
        return {}
    
    env = Environment()
    template = env.from_string(template_str)
    prompt = template.render(prompt=context.definition.prompt)

    return {"test": "result"}


@activity.defn
async def evaluate_step(context: StepContext) -> dict:
    if not isinstance(context.definition, EvaluateWorkflowStep):
        return {}
    
    #FIXME: set the field to keep source code
    source: str = context.definition.evaluate
    env = celpy.Environment()
    ast = env.compile(source)
    prog = env.program(ast)
    # TODO: set args
    args = {}
    result = prog.evaluate(args)
    return {"result": result}


@activity.defn
async def yield_step(context: StepContext) -> dict:
    if not isinstance(context.definition, YieldWorkflowStep):
        return {}
    
    #TODO: implement

    return {"test": "result"}


@activity.defn
async def tool_call_step(context: StepContext) -> dict:
    if not isinstance(context.definition, ToolCallWorkflowStep):
        return {}

    #TODO: implement

    return {"test": "result"}


@activity.defn
async def error_step(context: StepContext) -> dict:
    if not isinstance(context.definition, ErrorWorkflowStep):
        return {}

    return {"error": context.definition.error}


@activity.defn
async def if_else_step(context: StepContext) -> dict:
    if not isinstance(context.definition, IfElseWorkflowStep):
        return {}

    return {"test": "result"}


@activity.defn
async def transition_step(
    context: StepContext, start: tuple[str, int], result: dict
) -> dict:
    print("Running transition step")
    return {"test": "result"}
