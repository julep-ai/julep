#!/usr/bin/env python3


from datetime import timedelta

from temporalio import workflow

from agents_api.autogen.Executions import TransitionTarget
from agents_api.autogen.openapi_model import CreateTransitionRequest, TransitionType

with workflow.unsafe.imports_passed_through():
    from ..activities.task_steps import (
        evaluate_step,
        if_else_step,
        prompt_step,
        tool_call_step,
        transition_step,
        yield_step,
    )
    from ..autogen.openapi_model import (
        ErrorWorkflowStep,
        EvaluateStep,
        IfElseWorkflowStep,
        PromptStep,
        ToolCallStep,
        # WaitForInputStep,
        # WorkflowStep,
        YieldStep,
    )
    from ..common.protocol.tasks import (
        ExecutionInput,
        # OutcomeType,
        StepContext,
        StepOutcome,
        # Workflow,
    )


STEP_TO_ACTIVITY = {
    PromptStep: prompt_step,
    EvaluateStep: evaluate_step,
    ToolCallStep: tool_call_step,
    IfElseWorkflowStep: if_else_step,
    YieldStep: yield_step,
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
            current=start,
        )

        step_type = type(context.current_step)

        # 1. First execute the current step's activity if applicable
        if activity := STEP_TO_ACTIVITY.get(step_type):
            outcome = await workflow.execute_activity(
                activity,
                context,
                schedule_to_close_timeout=timedelta(seconds=600),
            )

        # 2. Then, based on the outcome and step type, decide what to do next
        #    (By default, exit if last otherwise transition 'step' to the next step)
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

        # 3. Orchestrate the step
        match context.current_step, outcome:
            case EvaluateStep(), StepOutcome(output=output):
                final_output = output
                transition_request = CreateTransitionRequest(
                    type=transition_type,
                    current=context.cursor,
                    next=next_target,
                    output=final_output,
                    metadata=metadata,
                )

                await workflow.execute_activity(
                    transition_step,
                    args=[context, transition_request],
                    schedule_to_close_timeout=timedelta(seconds=600),
                )

            case ErrorWorkflowStep(error=error), _:
                final_output = dict(error=error)
                transition_type = "error"
                transition_request = CreateTransitionRequest(
                    type=transition_type,
                    current=context.cursor,
                    next=None,
                    output=final_output,
                    metadata=metadata,
                )

                await workflow.execute_activity(
                    transition_step,
                    args=[context, transition_request],
                    schedule_to_close_timeout=timedelta(seconds=600),
                )

                raise Exception(f"Error raised by ErrorWorkflowStep: {error}")

            case YieldStep(), StepOutcome(
                output=output, transition_to=(transition_type, next)
            ):
                final_output = output
                transition_request = CreateTransitionRequest(
                    type=transition_type,
                    current=context.cursor,
                    next=next,
                    output=final_output,
                    metadata=metadata,
                )

                await workflow.execute_activity(
                    transition_step,
                    args=[context, transition_request],
                    schedule_to_close_timeout=timedelta(seconds=600),
                )

                yield_outcome: StepOutcome = await workflow.execute_child_workflow(
                    TaskExecutionWorkflow.run,
                    args=[execution_input, next, [output]],
                )

                final_output = yield_outcome.output

            case _:
                raise NotImplementedError()

        # 4. Closing
        # End if the last step
        if context.is_last_step:
            return final_output

        # Otherwise, recurse to the next step
        workflow.continue_as_new(
            execution_input, next_target, previous_inputs + [final_output]
        )

        ##################

        # should_wait, is_error = False, False
        # # Run the step
        # match step:
        #     case PromptStep():
        #         outputs = await workflow.execute_activity(
        #             prompt_step,
        #             context,
        #             schedule_to_close_timeout=timedelta(seconds=600),
        #         )
        #
        #         # TODO: ChatCompletion does not have tool_calls
        #         # if outputs.tool_calls is not None:
        #         #     should_wait = True

        #     case ToolCallStep():
        #         outputs = await workflow.execute_activity(
        #             tool_call_step,
        #             context,
        #             schedule_to_close_timeout=timedelta(seconds=600),
        #         )

        #     case IfElseWorkflowStep():
        #         outputs = await workflow.execute_activity(
        #             if_else_step,
        #             context,
        #             schedule_to_close_timeout=timedelta(seconds=600),
        #         )
        #         workflow_step = YieldStep(**outputs["goto_workflow"])
        #
        #         outputs = await workflow.execute_child_workflow(
        #             TaskExecutionWorkflow.run,
        #             args=[
        #                 execution_input,
        #                 (workflow_step.workflow, 0),
        #                 previous_inputs,
        #             ],
        #         )

        #     case WaitForInputStep():
        #         should_wait = True
