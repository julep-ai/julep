#!/usr/bin/env python3


from datetime import timedelta

from agents_api.autogen.Executions import TransitionTarget
from agents_api.autogen.openapi_model import CreateTransitionRequest
from temporalio import workflow

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
        WaitForInputStep,
        YieldStep,
    )

    from ..common.protocol.tasks import (
        ExecutionInput,
        StepContext,
        StepOutcome,
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
        workflow_map = {wf.name: wf.steps for wf in execution_input.task.workflows}

        current_workflow = workflow_map[start.workflow]
        step = current_workflow[start.step]
        step_type = type(step)

        context = StepContext[step_type](
            developer_id=execution_input.developer_id,
            execution=execution_input.execution,
            task=execution_input.task,
            agent=execution_input.agent,
            user=execution_input.user,
            session=execution_input.session,
            tools=execution_input.tools,
            arguments=execution_input.arguments,
            definition=step,
            inputs=previous_inputs,
        )

        next = None
        outcome = None
        activity = STEP_TO_ACTIVITY.get(step_type)
        final_output = None
        is_last = False

        if activity:
            outcome = await workflow.execute_activity(
                activity,
                context,
                schedule_to_close_timeout=timedelta(seconds=600),
            )

        match step, outcome:
            case YieldStep(), StepOutcome(output=output, transition_to=(transition_type, next)):
                transition_request = CreateTransitionRequest(
                    type=transition_type,
                    current=start,
                    next=next,
                    output=output,
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

        is_last = start.step + 1 == len(current_workflow)

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

        #         # TODO: ChatCompletion does not have tool_calls
        #         # if outputs.tool_calls is not None:
        #         #     should_wait = True

        #     case EvaluateStep():
        #         outputs = await workflow.execute_activity(
        #             evaluate_step,
        #             context,
        #             schedule_to_close_timeout=timedelta(seconds=600),
        #         )
        #     case YieldStep():
        #         outputs = await workflow.execute_child_workflow(
        #             TaskExecutionWorkflow.run,
        #             args=[execution_input, (step.workflow, 0), previous_inputs],
        #         )
        #     case ToolCallStep():
        #         outputs = await workflow.execute_activity(
        #             tool_call_step,
        #             context,
        #             schedule_to_close_timeout=timedelta(seconds=600),
        #         )
        #     case ErrorWorkflowStep():
        #         is_error = True
        #     case IfElseWorkflowStep():
        #         outputs = await workflow.execute_activity(
        #             if_else_step,
        #             context,
        #             schedule_to_close_timeout=timedelta(seconds=600),
        #         )
        #         workflow_step = YieldStep(**outputs["goto_workflow"])

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

        # # Transition type
        # transition_type = (
        #     "awaiting_input"
        #     if should_wait
        #     else ("finish" if is_last else ("error" if is_error else "step"))
        # )

        # # Transition to the next step
        # transition_info = TransitionInfo(
        #     from_=(wf_name, step_idx),
        #     to=None if (is_last or should_wait) else (wf_name, step_idx + 1),
        #     type=transition_type,
        # )

        # await workflow.execute_activity(
        #     transition_step,
        #     args=[
        #         context,
        #         transition_info,
        #         "failed" if is_error else "awaiting_input",
        #     ],
        #     schedule_to_close_timeout=timedelta(seconds=600),
        # )

        # # FIXME: this is just a demo, we should handle the end of the workflow properly
        # # -----

        # # End if the last step
        # if is_last:
        #     return outputs

        # # Otherwise, recurse to the next step
        # workflow.continue_as_new(
        #     execution_input, (wf_name, step_idx + 1), previous_inputs + [outputs]
        # )
