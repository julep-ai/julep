#!/usr/bin/env python3


import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from ..activities.task_steps import (
        evaluate_step,
        if_else_step,
        prompt_step,
        return_step,
        tool_call_step,
        transition_step,
        yield_step,
    )
    from ..autogen.openapi_model import (
        CreateTransitionRequest,
        ErrorWorkflowStep,
        EvaluateStep,
        IfElseWorkflowStep,
        PromptStep,
        ReturnStep,
        SleepFor,
        SleepStep,
        ToolCallStep,
        TransitionTarget,
        TransitionType,
        # WaitForInputStep,
        # WorkflowStep,
        YieldStep,
    )
    from ..common.protocol.tasks import (
        ExecutionInput,
        StepContext,
        StepOutcome,
        # Workflow,
    )
    from ..env import testing


STEP_TO_ACTIVITY = {
    PromptStep: prompt_step,
    EvaluateStep: evaluate_step,
    ToolCallStep: tool_call_step,
    IfElseWorkflowStep: if_else_step,
    YieldStep: yield_step,
    ReturnStep: return_step,
}


@workflow.defn
class TaskExecutionWorkflow:
    @workflow.run
    async def run(
        self,
        execution_input: ExecutionInput,
        start: TransitionTarget = TransitionTarget(workflow="main", step=0),
        previous_inputs: list[dict] = [],
    ) -> None:
        previous_inputs = previous_inputs or [execution_input.arguments]

        context = StepContext(
            execution_input=execution_input,
            inputs=previous_inputs,
            cursor=start,
        )

        step_type = type(context.current_step)
        outcome = None

        # 1. First execute the current step's activity if applicable
        if activity := STEP_TO_ACTIVITY.get(step_type):
            outcome = await workflow.execute_activity(
                activity,
                context,
                # TODO: This should be a configurable timeout everywhere based on the task
                schedule_to_close_timeout=timedelta(seconds=3 if testing else 600),
            )

        # 2a. Then, based on the outcome and step type, decide what to do next
        #     (By default, exit if last otherwise transition 'step' to the next step)
        final_output = None
        transition_type: TransitionType
        next_target: TransitionTarget | None
        metadata: dict = {"step_type": step_type.__name__}

        if context.is_last_step:
            transition_type = "finish"
            next_target = None

        else:
            transition_type = "step"
            next_target = TransitionTarget(
                workflow=context.cursor.workflow, step=context.cursor.step + 1
            )

        # 2b. Prep a transition request
        async def transition():
            # NOTE: The variables are closured from the outer scope
            transition_request = CreateTransitionRequest(
                type=transition_type,
                current=context.cursor,
                next=next_target,
                output=final_output,
                metadata=metadata,
            )

            return await workflow.execute_activity(
                transition_step,
                args=[context, transition_request],
                schedule_to_close_timeout=timedelta(seconds=600),
            )

        # 3. Orchestrate the step
        match context.current_step, outcome:
            case ReturnStep(), StepOutcome(output=output):
                final_output = output
                transition_type = "finish"
                await transition()

            case SleepStep(
                sleep=SleepFor(
                    seconds=seconds,
                    minutes=minutes,
                    hours=hours,
                    days=days,
                )
            ), _:
                seconds = seconds + minutes * 60 + hours * 60 * 60 + days * 24 * 60 * 60
                assert seconds > 0, "Sleep duration must be greater than 0"

                final_output = await asyncio.sleep(
                    seconds, result=context.current_input
                )

                await transition()

            case EvaluateStep(), StepOutcome(output=output):
                final_output = output
                await transition()

            case ErrorWorkflowStep(error=error), _:
                final_output = dict(error=error)
                transition_type = "error"
                await transition()

                raise ApplicationError(f"Error raised by ErrorWorkflowStep: {error}")

            case YieldStep(), StepOutcome(
                output=output, transition_to=(yield_transition_type, yield_next_target)
            ):
                # Save the original transition state
                original_next_target = next_target
                original_transition_type = transition_type

                final_output = output
                transition_type = yield_transition_type
                next_target = yield_next_target

                await transition()

                yield_outcome: StepOutcome = await workflow.execute_child_workflow(
                    TaskExecutionWorkflow.run,
                    args=[execution_input, yield_next_target, [output]],
                )

                # Restore the next target to the original value
                next_target = original_next_target
                transition_type = original_transition_type

                final_output = yield_outcome

            case _:
                raise NotImplementedError()

        # 4. Closing
        # End if the last step
        if transition_type in ("finish", "cancelled"):
            return final_output

        # Otherwise, recurse to the next step
        # TODO: Should use a continue_as_new workflow ONLY if the next step is a conditional or loop
        #       Otherwise, we should just call the next step as a child workflow
        workflow.continue_as_new(
            args=[execution_input, next_target, previous_inputs + [final_output]]
        )
