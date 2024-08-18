from typing import Callable

from beartype import beartype
from temporalio import activity

from agents_api.autogen.Executions import TransitionTarget

from ...common.protocol.tasks import StepContext, StepOutcome
from ...env import testing
from .utils import simple_eval_dict


@beartype
async def yield_step(context: StepContext) -> StepOutcome:
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


# Note: This is here just for clarity. We could have just imported yield_step directly
# They do the same thing, so we dont need to mock the yield_step function
mock_yield_step: Callable[[StepContext], StepOutcome] = yield_step

yield_step: Callable[[StepContext], StepOutcome] = activity.defn(name="yield_step")(
    yield_step if not testing else mock_yield_step
)