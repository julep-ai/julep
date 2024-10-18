from typing import Callable

from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import TransitionTarget, YieldStep
from ...common.protocol.tasks import StepContext, StepOutcome
from ...common.storage_handler import auto_blob_store
from ...env import testing
from .base_evaluate import base_evaluate


@auto_blob_store
@beartype
async def yield_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, YieldStep)

        all_workflows = context.execution_input.task.workflows
        workflow = context.current_step.workflow
        exprs = context.current_step.arguments

        assert workflow in [
            wf.name for wf in all_workflows
        ], f"Workflow {workflow} not found in task"

        # Evaluate the expressions in the arguments
        arguments = await base_evaluate(exprs, context.model_dump())

        # Transition to the first step of that workflow
        transition_target = TransitionTarget(
            workflow=workflow,
            step=0,
        )

        return StepOutcome(output=arguments, transition_to=("step", transition_target))

    except BaseException as e:
        activity.logger.error(f"Error in yield_step: {e}")
        return StepOutcome(error=str(e))


# Note: This is here just for clarity. We could have just imported yield_step directly
# They do the same thing, so we dont need to mock the yield_step function
mock_yield_step: Callable[[StepContext], StepOutcome] = yield_step

yield_step: Callable[[StepContext], StepOutcome] = activity.defn(name="yield_step")(
    yield_step if not testing else mock_yield_step
)
