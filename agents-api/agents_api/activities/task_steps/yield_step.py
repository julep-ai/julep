from typing import Any

from beartype import beartype
from temporalio import activity

from agents_api.autogen.Executions import TransitionTarget

from ...autogen.openapi_model import (
    YieldStep,
)
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from .utils import simple_eval_dict


@activity.defn
@beartype
async def yield_step(context: StepContext[YieldStep]) -> StepOutcome[dict[str, Any]]:
    all_workflows = context.execution_input.task.workflows
    workflow = context.current_step.workflow

    assert workflow in [
        wf.name for wf in all_workflows
    ], f"Workflow {workflow} not found in task"

    # Evaluate the expressions in the arguments
    exprs = context.current_step.arguments
    arguments = simple_eval_dict(exprs, values=context.model_dump())

    # Transition to the first step of that workflow
    transition_target = TransitionTarget(
        workflow=workflow,
        step=0,
    )

    return StepOutcome(output=arguments, transition_to=("step", transition_target))
