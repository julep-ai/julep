from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import TransitionTarget, YieldStep
from ...common.protocol.tasks import ExecutionInput, StepContext, StepOutcome
from .base_evaluate import base_evaluate


@activity.defn
@beartype
async def yield_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, YieldStep)

        if not isinstance(context.execution_input, ExecutionInput):
            raise TypeError("Expected ExecutionInput type for context.execution_input")

        all_workflows = context.execution_input.task.workflows
        workflow = context.current_step.workflow
        exprs = context.current_step.arguments

        assert workflow in [
            wf.name for wf in all_workflows
        ], f"Workflow {workflow} not found in task"

        # Evaluate the expressions in the arguments
        arguments = await base_evaluate(exprs, await context.prepare_for_step())

        # Transition to the first step of that workflow
        transition_target = TransitionTarget(
            workflow=workflow,
            step=0,
        )

        return StepOutcome(output=arguments, transition_to=("step", transition_target))

    except BaseException as e:
        activity.logger.error(f"Error in yield_step: {e}")
        return StepOutcome(error=str(e))
