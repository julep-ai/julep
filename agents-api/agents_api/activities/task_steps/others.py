# import celpy

# from temporalio import activity
# from uuid import uuid4


# from ...common.protocol.tasks import (
#     StepContext,
#     TransitionInfo,
# )


# from ...models.execution.create_execution_transition import (
#     create_execution_transition_query,
# )


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
